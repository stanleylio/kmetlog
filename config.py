
#data_dir = '/var/logging/data'
#log_dir = '/var/logging/log'

# hard-code these instead
# I get to assign them whatever I want, they're not going to change
#kmet_port = 9002
#service_discovery_port = 9005


config = {
    'kmet-bbb':{'subscribeto':['localhost','192.168.1.167'],
                'private_key_file':'/root/.ssh/id_rsa',
                'data_dir':'/var/logging/data',
                'log_dir':'/var/logging/log'},

    'kmet-bbb-wind':{'subscribeto':['localhost','192.168.1.109'],
                     'private_key_file':'/root/.ssh/id_rsa',
                     'data_dir':'/var/logging/data',
                     'log_dir':'/var/logging/log'}
          }

