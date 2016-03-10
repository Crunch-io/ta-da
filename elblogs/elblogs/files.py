import os
import re
import subprocess

FIELDS = 'timestamp elb client:port backend:port request_processing_time backend_processing_time response_processing_time elb_status_code backend_status_code received_bytes sent_bytes request_verb request_url request_protocol user_agent ssl_cipher ssl_protocol'.split(' ')
NUMERIC_FIELDS = 'request_processing_time backend_processing_time response_processing_time elb_status_code backend_status_code received_bytes sent_bytes'.split(' ')

re_dataset_id = re.compile(".*/api/datasets/([0-9a-f]+).*")

def find_dot(start=None, end=None, path="."):
    ''' Find all log files, perhaps filtered by a date range, as 8 digit
        integers or as strings like "20151230T1100"'''
    files = []
    if start and "T" in start:
        startdate, starttime = (int(x) for x in start.split("T"))
    else:
        starttime = None
        startdate = start
        if startdate:
            startdate = int(startdate)
    if end and "T" in end:
        enddate, endtime = (int(x) for x in end.split("T"))
    else:
        endtime = None
        enddate = end
        if enddate:
            enddate = int(enddate)
    for dirpath, dirnames, filenames in os.walk(path):
        files.extend([os.path.join(dirpath, name) for name in filenames
            if name[-4:] == ".log" and
            file_in_date_range(name, startdate, enddate, starttime, endtime)])
    files.sort()
    return files

def file_in_date_range(filename, startdate=None, enddate=None, starttime=None, endtime=None):
    ''' Given a file name format like '910774676937_elasticloadbalancing_eu-west-1_eu-vpc_20151101T2300Z_52.19.22.234_16gycro6.log',
        parse the date and do math on it to determine whether it is in the
        specified range.
    '''
    out = True
    if startdate or enddate:
        try:
            timestamp = filename.split("_")[4]
            date, time = int(timestamp[:8]), int(timestamp[9:13])
            if startdate:
                out &= date >= startdate
                if date == startdate and starttime:
                    out &= time >= starttime
            if enddate:
                out &= date <= enddate
                if date == enddate and endtime:
                    out &= time <= endtime
        except:
            print "Error parsing filename", filename
            out = False
    return out

def load_log(filename):
    '''Take an ELB file and return a data.frame-like dict of columns'''
    with open(filename) as f:
        cols = zip(*(line.split(' ') for line in f))
    out = dict(zip(FIELDS, cols))
    for i in NUMERIC_FIELDS:
        ## Make these numeric so we can do math on them
        out[i] = [float(x) for x in out[i]]
    return out

def logfile_to_datasets(filenames, destination):
    ''' Take an ELB file or list of files, split its entries by which dataset,
        and append to the appropriate dataset-specific file
    '''

    if isinstance(filenames, basestring):
        filenames = [filenames]
    destfiles = {}
    processed_filename = os.path.join(destination, "processed_logs")
    if os.path.isfile(processed_filename):
        with open(processed_filename) as f:
            already_done = set(os.path.basename(line.strip()) for line in f.readlines())
    else:
        already_done = set([])
    with open(processed_filename, "a") as processed:
        for filename in filenames:
            filebasename = os.path.basename(filename)
            if filebasename in already_done:
                continue
            with open(filename) as elb:
                for entry in elb:
                    dsid = extract_dataset_id(entry)
                    if dsid not in destfiles:
                        # Open file in append mode (also create if doesn't exist yet)
                        destfiles[dsid] = open(os.path.join(destination, dsid + ".log"), "a")
                    destfiles[dsid].write(entry)
            processed.write(filebasename + "\n")

    # Close the file connections
    for dsid, f in destfiles.iteritems():
        f.close()
        dsfile = os.path.join(destination, dsid + ".log")
        # Dedupe with bash `sort -u` in case it runs more than once
        # TODO: move this to analysis time
        # subprocess.call(["sort", "-u", dsfile, "-o", dsfile])

def extract_dataset_id(log_entry):
    '''Given an ELB log entry, search for a dataset id in the request URL'''
    m = re_dataset_id.match(log_entry)
    if m:
        return m.expand(r"\1")
    else:
        return "__none__"
