import sys
sys.path.append('/root/node')
from datetime import datetime
import logging,traceback
from display.gen_plot import plot_time_series
from os.path import join,basename


logging.basicConfig()


with open('/var/logging/log/spaceusage.log') as f:
    D = {}
    ts = None
    for line in f:
        line = line.strip()
        try:
            ts = datetime.strptime(line,'%Y-%m-%dT%H:%M:%SZ')
            continue
        except ValueError:
            logging.debug(traceback.format_exc())

        assert ts is not None
        line = line.split('\t')
        if line[1] not in D:
            D[line[1]] = []
        D[line[1]].append([ts,float(line[0])])


for k in D.keys():
    d = zip(*D[k])
    plot_time_series(d[0],[v/1e3 for v in d[1]],\
                     join('/var/www/km1app/km1app/static/img','space_' + basename(k) + '.png'),\
                     title=k,xlabel='Logger Time (UTC)',ylabel='Directory Size, MB',\
                     markersize=8)

