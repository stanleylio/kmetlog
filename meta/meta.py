from __future__ import division
import subprocess
import time


def execute(cmdaslist):
    p = subprocess.Popen(cmdaslist,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out,err = p.communicate()
    return out,err


out,_ = execute(['df'])
for row in out.strip().split('\n'):
    if row.endswith('/'):
        row = filter(lambda x: len(x),row.split(' '))
        total,used = row[1],row[3]

print '{},{},{}'.format(time.time(),total,used)
