# client_shared.py, shared client code

import os
import sys
import optparse

import logging
l = logging.getLogger()
l.setLevel(logging.WARNING)

adddir = os.path.join(os.getcwd(), 'source')
sys.path.insert(0, adddir)
from lib.network import object_sharer as objsh

parser = optparse.OptionParser()
parser.add_option('-d', '--disable-io', default=False, action='store_true')
parser.add_option('-p', '--port', type=int, default=objsh.PORT,
    help='Port to connect to')
parser.add_option('--name', default='',
    help='QTlab instance name to connect to, should be auto-detected')
parser.add_option('--host', default='localhost',
    help='Host to connect to')
parser.add_option('--module', default=None,
    help='Client module to import')
parser.add_option('--config', default=None,
    help='Set config file to use, defaults to <argv0>_<module>.cfg')
parser.add_option('--debug', default=False, action='store_true',
    help='Enable debugging mode, ie more logging')

def process_args():
    args, pargs = parser.parse_args()

    if args.config is None:
        args.config = os.path.split(sys.argv[0])[-1]
        if args.config.endswith('.py'):
            args.config = args.config[:-3]
        if args.module:
            args.config += '_' + args.module + '.cfg'

    if args.config:
        import lib.config as cfg
        global config
        config = cfg.create_config(args.config)
    if args.name:
        config['instance_name'] = args.name
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    return args, pargs

def close_client_cb():
    pass

