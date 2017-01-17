import os
import signal
import sys
try:
    import select
    import fcntl
except (ImportError, NameError):
    select = None
    fcntl = None
import time
from subprocess import Popen, PIPE, STDOUT, call
import json


class ErroR(Exception):
    pass

# Define some templates for communicating with R.
# ===============================================
# We want to wrap any R that we are given in an error handler so that we get a
# useful error message out of R. We also want to ensure that R always outputs a
# newline after every command so that we can use a line-based algorithm to read
# our output. The WRAP template does this for us (and the ERROR string is used
# on the far side to parse error responses). 

# In order for the error handlers to ever be able to work, however, we need to
# ensure that the unfoldR_run() function that wraps the R syntax can never fail.
# If we just inserted R code into the body of that function, and the R code were
# syntactically invalid, the unfoldR_run() function would error on creation, and 
# that erroring would happen outside of the tryCatch() with the error handler.
# So, we need to pass in the R code as a string and parse it in R. We also need
# to escape any quotes and stuff in the R code. Below, in Rprocess.run, we 
# JSONify the R syntax we're going to run twice: once to deparse it and once to
# escape it. The R wrapper function unfoldR_run() deserializes with fromJSON()
# and then parses the string. If the R syntax is invalid, this parsing, which
# happens when unfoldR_run is evaluated, not when it is initialized, will 
# throw an error that will properly be caught.

# When we send commands to R, it echoes these back to us using "> " as its
# prompt and "+ " as a prefix for continuation lines. It looks like this:

#   > unfoldR_run <- function () {
#   +     do.this.stuff <- parse(text=fromJSON("[\"some_R_stuff()"]"))
#   +     eval(do.this.stuff, envir=.GlobalEnv) 
#   +     cat("\n")
#   + }
#   >

# We don't want to return the echoed input back to our own caller, so we use
# the START_ and STOP_READING strings to determine which output we actually
# want. We want the output between the last two lines of WRAP, basically.

ERROR = "!!Error: "
INIT = """unfoldR_run <- function (x) {
    do.this.stuff <- parse(text=jsonlite::fromJSON(do.call("paste0", x)))
    eval(do.this.stuff, envir=.GlobalEnv)
    cat("\\n")
}

unfoldR_err <- function (e) {
    cat("%s", e$message, "\\n")
}
aRgs <- list()
""" % ERROR

RUN = """
tryCatch(unfoldR_run(aRgs), error=unfoldR_err)
invisible("unfoldR over and out")
"""

RPIPE = "aRgs[[length(aRgs)+1]] <- %s\n"

START_READING = "> " + RUN.splitlines()[-2] + "\n"
STOP_READING  = "> " + RUN.splitlines()[-1] + "\n"

# We also want to know deterministically when .Rprofile has finished and the 
# process is ready.
FINISHED_STARTING = "> "

CHUNK_SIZE = 1024*2 # 2K

def chunk_string(s, maxchars):
    """Converts a long string into a list with lines of length < maxchars
    and makes sure that words are not split in the middle"""
    words = s.strip('"').split(' ')
    words.reverse()
    res = []
    line_length = 0
    line = []
    fmt_line = lambda l: '"%s "' % ' '.join(l)
    while words:
        word = words.pop()
        w_len = len(word) + 1 # account for the joined space
        if line_length + w_len > maxchars:
            res.append(fmt_line(line))
            line_length = 0
            line = []

        line.append(word)
        line_length += w_len
    res.append(fmt_line(line))
    return res


class RProcess(object):
    """An R process."""

    linesep = os.linesep

    def __init__(self, process, settings):
        """Takes a Popen process
        """
        assert isinstance(process, Popen)
        self.settings = settings
        self.process = process
        self.inactive_timeout = 0
        self.time_of_birth = time.time()
        if fcntl:
            fd = self.process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def serialize(self):
        """Return enough info that we can reconnect after death.
        """
        return ( self.process.pid
               , self.process.stdin.fileno()
               , self.process.stdout.fileno()
                )

    @property
    def pid(self):
        return self.process.pid

    def log(self, message):
        msg = "R-pid-%s %s"
        msg %= self.process.pid, message
        some_limit = 72
        if 0 and len(msg) > some_limit:
            # XXX Make this an option?
            msg = msg[:some_limit-3] + "..."
        print msg

    @classmethod
    def birth(cls, settings={}, args=['R']):
        """Given args, launch an R process.
        """
        cmd = args[:]
        for arg in ('--no-save', '--no-restore'):
            if arg not in cmd:
                cmd.append(arg)
        if '--encoding' not in cmd:
            cmd.append('--encoding')
            cmd.append('utf8')

        print "Invoking R: %s" % (' '.join(cmd))
        # stderr = sys.stderr.fileno() # assume fileno()
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)#, stderr=stderr, env=ENV)
        R = cls(process, settings)
        R.log("Birthing.")
        time.sleep(2)

        # Wait until .Rprofile has completed before returning the RProcess
        # object. While .Rprofile is being run, R ignores SIGINT. Allowing
        # .Rprofile to run therefore gives us more predictable SIGINT behavior.
        # while R.readline() != FINISHED_STARTING:
        #     time.sleep(0.05)

        return R

    def run(self, command):
        """Pass the given string to R and return its output.
        """

        self.log("running " + command)
        # Use json.dumps to escape the quoting in the command
        # Wrap the string in a [] because R seems to like that better,
        # and anyway it doesn't distinguish between objects and arrays
        # of length one
        escaped_command = json.dumps(json.dumps([command]))
        #self.log("Fed to R:")
        #self.log(WRAP % escaped_command)
        # self.write(WRAP % escaped_command)
        self.write(INIT)

        maxchar = CHUNK_SIZE
        if len(escaped_command) > maxchar:
            escaped_command = chunk_string(escaped_command, maxchar)
        else:
            escaped_command = [ escaped_command ]

        for i in escaped_command:
            self.log(RPIPE % i)
            self.write(RPIPE % i)

        self.write(RUN)

        output = self.readall()

        self.log("returned " + output)
        if output.startswith(ERROR):
            m = output[len(ERROR):] + "\ncommand: " + command
            raise ErroR(m.encode('utf-8'))
        return output

    def readall(self):
        """Return R's response to our command. See comments on WRAP above.
        """

        # Discard garbage output.
        while self.readline() != START_READING:
            pass

        # Capture the output we're interested in.
        buf = []
        while True:
            line = self.readline()
            if line == STOP_READING:
                break
            buf.append(line)
        buf = "".join(buf)

        return buf

    if select and fcntl:
        # Non-blocking version
        readline_timeout = 30.0 * 60 # Half hour
        readline_rbufsize = 1024
        readline_buffer = ""
        def readline(self):
            """Return one line of the R process output as a string.
            """
            while True:
                if "\n" in self.readline_buffer:
                    line, self.readline_buffer = self.readline_buffer.split("\n", 1)
                    try:
                        out = line.decode('utf8') + u'\n'
                    except UnicodeDecodeError, exc:
                        # This line was not fully utf8 encoded, wtf
                        out = line.decode('utf8', 'ignore') + u'\n'
                        self.log('Failed to decode line:')
                        self.log(out)
                        self.log('Proceeded to ignore troubling chars: %s' % str(exc))

                    #sys.stdout.write(out); sys.stdout.flush() # for debugging
                    return out

                try:
                    things = select.select([self.process.stdout],
                                           [],
                                           [self.process.stdout],
                                           self.readline_timeout)
                except select.error, err:
                    if err.args[0] == errno.EINTR:
                        continue # Interrupted system call. Try again!
                    raise
                readable, writeable, errored = things

                if not (readable or writeable or errored):
                    m = "%d-minute timeout expired."
                    m %= self.readline_timeout / 60
                    raise IOError(m)

                # Read from the pipe
                for sock in readable:
                    try:
                        # XXX Why do we not use sock in here, other than to
                        # maybe close it? Is sock equivalent (or identical?) to
                        # self.process.stdout?
                        data = os.read(self.process.stdout.fileno(),
                                       self.readline_rbufsize)
                        if not data:
                            sock.close()
                            raise IOError("select: no data")
                    except OSError, err:
                        if err.errno == errno.EAGAIN:
                            self.log("bailing out on EAGAIN")
                            # We'll revisit this readable socket again on the
                            # next pass through select.
                            continue
                        raise
                    self.readline_buffer += data

                # Handle exceptions
                for sock in errored:
                    sock.close()
                    raise IOError("select: exception")
    else:
        # Blocking version
        def readline(self):
            """Return one line of the R process output as a string."""
            return self.process.stdout.readline().decode('utf8')


    def write(self, u):
        """Write the given unicode string to the R process."""
        self.process.stdin.write(u.encode('utf8'))
        self.process.stdin.flush()

    def close(self):
        """Close the R process by sending SIGTERM.

        There's a SIGCHLD handler in foldR.py that will clean up that module's
        data structures after the process exits.

        """
        self.log("Sending TERM to %d." % self.process.pid)
        os.kill(self.process.pid, signal.SIGTERM)
