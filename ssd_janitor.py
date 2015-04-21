#!/usr/bin/env python

import os
import time
from itertools import izip

datadir='/scratch0/zz9data/'

dirs = os.listdir(datadir)

atimes = [(os.stat(datadir+d+'/atime').st_mtime, d) for d in dirs]
mtimes = [(os.stat(datadir+d+'/mtime').st_mtime, d) for d in dirs]
info = {d: (m, a) for ((a,d),(m,_)) in izip(atimes, mtimes)}

atimes.sort()

N = 10

def get_avail():
    p = os.popen('df -Ph %s' % datadir)
    result = p.read()
    status = p.close()
    if status or not result:
        return None
    tok = result.split('\n')[1].split()
    free = tok[3]
    if free.endswith('G'):
        return float(free[:-1])
    else:
        raise ValueError(free)

def get_s3_mtime(fname):
    p = os.popen('s3ls.py ' + fname)
    result = p.read()
    status = p.close()
    if status or not result:
        return None
    tok = result.split('\n')[0].split()
    timestamp = tok[2]
    if timestamp.endswith('Z'):
        timestamp = timestamp[:-1]
    timestamp, msec = timestamp.split('.')
    return time.mktime(time.strptime(
        timestamp, '%Y-%m-%dT%H:%M:%S')) + float('0.'+msec)

    return tok[2]

for a,d in atimes:
    print
    print 'available space: ', get_avail(), "GB"
    print
    print 'dataset', d
    print 'mtime', time.ctime(info[d][0])
    print 'atime', time.ctime(info[d][1])
    stime = get_s3_mtime(d)
    print 'stime',time.ctime(stime)
    print 'delta_t', info[d][0] - stime
    cmd = 'rm -r %s/%s' % (datadir, d)
    reply = raw_input('delete local copy? ')
    if reply.lower().startswith('y'):
        reply = raw_input('run %s ' % cmd)
        if reply.lower().startswith('y'):
            os.system(cmd)
    elif reply.lower().startswith('q'):
        break
