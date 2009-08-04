import logging
import config

logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(name)-12s: %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filename=os.path.join(config.get_workdir(), 'qtlab.log'),
    filemode='a+')

def _setup_logging():
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(name)s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def set_debug(enable):
    if enable:
        logging.basicConfig(level=logging.DEBUG)
        logging.info('Set logging level to DEBUG')
    else:
        logging.basicConfig(level=logging.INFO)
        logging.info('Set logging level to INFO')

_setup_logging()
