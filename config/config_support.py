#
# Stanley H.I. Lio
# hlio@hawaii.edu
# All Rights Reserved. 2017
import re,socket,traceback
from importlib import import_module
from socket import gethostname


def import_node_config():
    f = gethostname().replace('-','_')
    return import_module('config.{}'.format(f))


if '__main__' == __name__:
    pass
