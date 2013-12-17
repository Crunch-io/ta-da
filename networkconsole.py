#!/usr/bin/env python

import sys
import socket
import code
import threading

_stdout, _stderr = sys.stdout, sys.stderr
_ps1, _ps2 = '>>>', '...'

class Diverter:
    def __init__(self, sock):
        self.sock = sock

    def write(self, line):
        try:
            self.sock.send(line)
        except Exception, e:
            print >> _stderr, e
            print >> _stdout, line

class NetworkConsole(code.InteractiveConsole, threading.Thread):

    def __init__(self, port=13013):
        self.port = port
        code.InteractiveConsole.__init__(self)
        threading.Thread.__init__(self)

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('0.0.0.0', self.port))
        self.sock.listen(1)
        self.lines = []
        self.partial_line = ""
        while True:
            try:
                self.conn, self.remote_addr = self.sock.accept()
                #self.f = self.conn.makefile()
                sys.stdout = Diverter(self.conn) # Yikes, is this the only way to capture output?
                sys.ps1 = 'zz9'+_ps1
                sys.ps2 = 'zz9'+_ps2
                self.interact("You are connected to a running zz9 instance, so be careful!")
            except Exception, e:
                print >> _stderr, e
            finally:
                sys.stdout = _stdout
                sys.ps1 = _ps1
                sys.ps2 = _ps2
                try:
                    self.conn.close()
                except:
                    pass


    def write(self, line): # Note, this only handles stderr!
        try:
            self.conn.send(line)
        except Exception, e:
            print >> _stderr, e

    def raw_input(self, prompt):
        while not self.lines:
            if prompt:
                if not prompt.endswith(' '):
                    prompt += ' '
                try:
                    self.conn.send(prompt)
                except Exception, e:
                    print >> _stderr,  e
            try:
                data = self.partial_line + self.conn.recv(8192)
                if data and data.startswith('\004'):
                    raise EOFError
            except Exception, e:
                print >> _stderr, e
                data = None
            if not data:
                raise EOFError
            lines = data.split('\r\n') # telnet
            self.partial_line = lines.pop() # if data ends with \n this is empty
            self.lines.extend(lines)

        line = self.lines.pop(0)
        if any(line.startswith(x) for x in ('\004', 'quit', 'sys.exit', 'exit')):
            # Don't quit the interpreter!
            raise EOFError
        if '\004' in line:
            return ''
        return line

    def __del__(self):
        try:
            self.sock.close()
        except:
            pass


if __name__=='__main__':
    nc = NetworkConsole()
    nc.start()
