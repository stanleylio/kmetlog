import subprocess
from datetime import datetime


def execute(cmdaslist):
    p = subprocess.Popen(cmdaslist,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out,err = p.communicate()
    return out,err


with open('/var/kmetlog/log/spaceusage.log','a') as f:
    f.write(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') + '\n')

    out,_ = execute(['du','-s','/var/kmetlog/data','/var/kmetlog/log'])
    print out.strip()
    f.write(out)
    
    out,_ = execute(['df'])
    for row in out.strip().split('\n'):
        if 'mmcblk0p1' in row:
            row = row.split(' ')
            row = filter(lambda x: len(x),row)
            row = '{sizeinbyte}\t{dirpath}'.format(sizeinbyte=row[2],dirpath=row[0])
            print row
            f.write(row + '\n')
