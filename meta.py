# python meta.py path_to_spaceusage.log output_dir_for_PNGs
import sys
sys.path.append('../node')
from datetime import datetime
import logging,traceback
from display.gen_plot import plot_time_series
from os.path import join,basename,exists
from helper import dt2ts


logging.basicConfig()

# the defaults
infile = '/var/kmetlog/log/spaceusage.log'
outdir = '/var/www/km1app/km1app/static/img'

if len(sys.argv) > 1:
    assert 3 == len(sys.argv)
    infile = sys.argv[1]
    outdir = sys.argv[2]
    assert exists(infile),infile
    assert exists(outdir),outdir


with open(infile) as f:
    D = {}
    ts = None
    for line in f:
        line = line.strip().replace('\0','')
        try:
            ts = datetime.strptime(line,'%Y-%m-%dT%H:%M:%SZ')
            continue
        except (TypeError,ValueError):
            logging.debug(traceback.format_exc())

        assert ts is not None
        line = line.split('\t')
        if line[1] not in D:
            D[line[1]] = []
        D[line[1]].append([ts,float(line[0])])
# hack
        while len(D[line[1]]) > 24*7*2:
            D[line[1]].pop(0)


for k in D.keys():
    try:
        print k
        
        d = zip(*D[k])
        tmp = [tmp[0] - tmp[1] for tmp in zip(d[1][1:],d[1][0:-1])]
        tmp = float(sum(tmp))/len(tmp)
        if tmp <= 1024:
            rate = tmp
            linelabel = '{:.1f} kB/hour'.format(rate)
        else:
            rate = tmp/1024.
            linelabel = '{:.1f} MB/hour'.format(rate)
        
        plot_path = join(outdir,'space_' + basename(k) + '.png')
        plot_time_series(d[0],[v/1024. for v in d[1]],\
                         plot_path,\
                         title=k,xlabel='Logger Time (UTC)',ylabel='Directory Size, MB',\
                         linelabel=linelabel,
                         markersize=8)
    except KeyboardInterrupt:
        break
    except:
        traceback.print_exc()
