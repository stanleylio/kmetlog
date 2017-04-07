# Service discovery stuff
#
# To run this as a daemon:
#   python service_discovery.py --service_offered service1:port1 service2:port2
#
# To initiate a search:
#   python service_discovery.py --search kmet1
#
# Three jobs:
#   It responds to requests from other hosts looking for services;
#   It listens for service announcements from other hosts and maintains a list of hosts offering that service;
#   It serves that list of hosts offering the 'kmet1' service for processes on this machine (though there's
#       nothing stopping the other hosts from querying for that list).
#
# ... wouldn't need this if DNS works...
#
# The Protocol (on UDP PORT):
# To find other hosts, broadcast the string (using topic='kmet1' as example)
#   {"service_query":"kmet1"}
# Publishers that get this message would respond with the string (using kmet-bbb as example)
#   {"hostname":"kmet-bbb","ip":"192.168.1.109","service_response":[["kmet1",9002],...]}
#
# For clients: to initiate a search for the kmet1 service, send to the daemon
#   {"get_service_listing":"kmet1","id":"some random unique string"}
# "id" is optional.
#
# - - - - -
# A publisher can publish multiple topics at multiple ports, and a subscriber can subscribe
# to multiple topics from multiple publishers.
# Basically N-to-N: "every host has sensor feeds that other hosts may read", and "every host
# is potentially interested in other feeds" - i.e. there's no longer fixed roles of
# "publisher" and "data logger".
#
# Yet there's still the decision to be made: after discovery, which of those am I actually
# interested in?
#
# In principle, this host does not need to maintain an up-to-date list of known hosts at all
# time - you can initiate a query broadcast only when such list is needed. Not storing a list
# also means nothing would go stale, so there's no timestamps to keep track of. Small delay,
# small price to pay.
#
# The host would still need a daemon to respond to query broadcasts from other hosts.
#
#
# Stanley H.I. Lio
# hlio@hawaii.edu
# Ocean Technology Group
# SOEST, University of Hawaii
# All Rights Reserved, 2017
import sys,json,subprocess,traceback,socket,logging,time,uuid
from twisted.internet.protocol import DatagramProtocol


PORT = 9005


def getIP():
    proc = subprocess.Popen(['hostname -I'],stdout=subprocess.PIPE,shell=True)
    out,err = proc.communicate()
    ips = out.strip().split(' ')
    ips = filter(lambda x: x != '192.168.7.2',ips)[0]
    return ips


class ServiceDiscovery(DatagramProtocol):
    _hostname = socket.gethostname()
    _publishers = {}     # all currently known publishers

    def __init__(self,service_offered):
        self._service_offered = service_offered
    
    def startProtocol(self):
        self.transport.setBroadcastAllowed(True)
    
    def datagramReceived(self,data,(host,port)):
        try:
            d = json.loads(data)

            if 'service_query' in d:
                if d['service_query'] not in [tmp[0] for tmp in self._service_offered]:
                    logging.debug('Not a service I offer: {}'.format(d['service_query']))
                    return

                logging.debug('Responding to query from ' + host)
                ip = getIP()
                d = {'hostname':self._hostname,'ip':ip,'service_response':self._service_offered}
                line = json.dumps(d,separators=(',',':'))
                self.transport.write(line,(host,port))

            if 'service_response' in d:
                if 'hostname' not in d:
                    logging.debug('missing "hostname": ' + data)
                    return
                if 'ip' not in d:
                    logging.debug('missing "ip": ' + data)
                    return
                if d['ip'] != host:
                    logging.debug('announcement not coming from the publisher itself: ' + data)
                    return
                
                self._publishers[d['ip']] = (time.time(),d['service_response'])

            if 'get_service_listing' in d:
                self.service_query(d['get_service_listing'])
                # query service providers on demand
                # problem is, the service_response won't get processed until this returns
                # so don't sleep, use callLater()

                self._publishers = {}
                line = json.dumps({'service_query':d['get_service_listing']},separators=(',',':'))
                self.transport.write(json.dumps(line,separators=(',',':')),(host,port))

                def callback():
                    tmp = {'service_listing':self.get_publisher_list()}
                    if 'id' in d:
                        tmp['id'] = d['id']
                    self.transport.write(json.dumps(tmp,separators=(',',':')),(host,port))
                reactor.callLater(d.get('max_response_time',1),callback)
        except:
            logging.debug(traceback.format_exc())
            logging.debug(data)

    def service_query(self,topic):
        """Query everyone for the given topic via UDP broadcast.
Whoever publishing this topic would respond with its own IP."""
        logging.debug('Broadcasting query...')
        #tag = uuid.uuid4().hex
        #self._ongoing_queries.append(tag)
        line = json.dumps({'service_query':topic},separators=(',',':'))
        self.transport.write(line,('<broadcast>',PORT))

    def get_publisher_list(self):
        '''# remove stale entries
        for ip in self._publishers:
            if time.time() - self._publishers[ip][0] > best_before:
                 del self._publishers[ip]'''
        
        # create a list
        pl = []
        for ip in self._publishers:
            services = self._publishers[ip][1]
            for service in services:
                pl.append('{}:{}'.format(ip,service[1]))
        return pl

def get_publisher_list(service,max_response_time=1):
    """Ask the local daemon for a list of known hosts with the given service"""
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #sock.settimeout(max_response_time)
    sock.settimeout(1)  # this is waiting for the daemon, not the daemon waiting for other hosts.
    tag = uuid.uuid4().hex
    tmp = {'get_service_listing':service,'max_response_time':max_response_time,'id':tag}
    tmp = json.dumps(tmp,separators=(',',':'))
    sock.sendto(tmp,('127.0.0.1',PORT))
    logging.debug('waiting for response...')
    try:
        i = 0
        while True: # wait for daemon response; ignore other traffic
            try:
                d,h = sock.recvfrom(1024)
                logging.debug(d + ' from ' + repr(h))
                tmp = json.loads(d)
                # id is optional - accept anything if id is not included
                if 'service_listing' in tmp and tmp.get('id',tag) == tag:
                    return tmp['service_listing']
            except socket.timeout:
                i += 1
                logging.debug('waiting for daemon {}'.format(i))
                if i >= 5:
                    logging.error('Daemon not running / timeout. "python service_discovery.py" if daemon is not running.')
                    return []
    except:
        logging.error(traceback.format_exc())
    return []


if '__main__' == __name__:
    from twisted.internet import reactor
    import argparse

    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='Service discovery related.')
    parser.add_argument('--service_offered',default=[],nargs='+',\
                        help='Example: --service_offered kmet1:9002 debug2:9003 ...')
    parser.add_argument('--search',help='Example: --search kmet1')
    args = parser.parse_args()

    #print(args.search)

    # --service_offered is to be kmet1:9002 debug2:9003 ...
    # service_offered is to be [(service_name,port2),(service2_name,port2),...]

    service_offered = [tmp.split(':') for tmp in args.service_offered]
    service_offered = [(tmp[0],int(tmp[1])) for tmp in service_offered]
    #print(service_offered)
    #service_offered = [('kmet1',9002)]
    
    if args.search is None:
        p = ServiceDiscovery(service_offered)
        reactor.listenUDP(PORT,p)
        reactor.run()
    else:
        R = get_publisher_list(args.search,max_response_time=3)
        for r in R:
            print(r)
        if len(R) <= 0:
            print('No service provider found.')
