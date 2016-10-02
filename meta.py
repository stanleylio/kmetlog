# plot spaceusage.log
import sys
sys.path.append('../node')
from datetime import datetime
import logging,traceback
from display.gen_plot import plot_time_series
from os.path import join,basename,exists
from helper import dt2ts


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
# hack
        while len(D[line[1]]) > 24*14:
            D[line[1]].pop(0)


for k in D.keys():
    d = zip(*D[k])
    tmp = [tmp[0] - tmp[1] for tmp in zip(d[1][1:],d[1][0:-1])]
    tmp = float(sum(tmp))/len(tmp)
    if tmp <= 1024:
        rate = tmp
        linelabel = '{:.1f} kB/hour'.format(rate)
    else:
        rate = tmp/1024.
        linelabel = '{:.1f} MB/hour'.format(rate)
    
    plot_path = join('/var/www/km1app/km1app/static/img','space_' + basename(k) + '.png')
    if not exists(plot_path):
        plot_path = join('/var/logging/log','space_' + basename(k) + '.png')
    plot_time_series(d[0],[v/1024. for v in d[1]],\
                     plot_path,\
                     title=k,xlabel='Logger Time (UTC)',ylabel='Directory Size, MB',\
                     linelabel=linelabel,
                     markersize=8)
