from GCClient import GCClient
from GCClient_CustomFormatter import UTCFormatter
import time
import logging
import logging.config

import argparse
import sys
import GC_Utility
import json


# Setup Main:
def main(argv):
    # Main Variables:
    Version = '2017_patch8'
    AppName = 'Graycell Client'
    LoggerName = 'gcclient'

    # Command Line Argument Parsing:
    parser = argparse.ArgumentParser(description='Graycell Client Executor', add_help=True)
    parser.add_argument('-v','--version', action='version', version=Version)
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Turn on debug mode')
    parser.add_argument('--disable_comms', dest='disable_comms', action='store_false', default=True, help='Turn off communicaitons')
    parser.add_argument('-i', '--client_id', dest='client_id', default=None, help='Specify Client ID String')
    parser.add_argument('-c', '--conf', dest='conf', default='gcclient.ini', help='Specify Client Configuration File')
    parser.add_argument('-l', '--logging_conf', dest='logging_conf', default=None, help='Specify Client Logging Configuration File')
    parser.add_argument('-ah', '--amqp_host', dest='amqp_host', default=None, help='AMQP Hostname or IP Address')
    parser.add_argument('-ap', '--amqp_port', dest='amqp_port', default=5672, type=int, help='AMQP Port Number')
    parser.add_argument('-as', '--amqp_ssl_on', dest='amqp_ssl_on', action='store_true', default=False, help='Turn on AMQP SSL')
    parser.add_argument('--test', dest='test_client', action='store_true', default=False, help='Run stand-alone tests')

    args = parser.parse_args()

    # Setup Logging:
    # Read Logging Config File or use built in version:
    if args.logging_conf is not None:
        config_file = open(args.logging_conf)

        with config_file as fd:
            gc_logging_conf = yaml.load(fd)

        config_file.close()

        # Load the logging config:
        logging.config.dictConfig(gc_logging_conf['logging'])
        logger = logging.getLogger(LoggerName)

    else:
        # Use built in logging configuration:
        # create logger
        logger = logging.getLogger(LoggerName)

        # create console handler and set level to debug
        ch = logging.StreamHandler()

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s :: %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        if args.debug:
            logger.setLevel(logging.DEBUG)
            ch.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            ch.setLevel(logging.INFO)

        # add ch to logger
        logger.addHandler(ch)

    # Print out the args to verify them:
    logger.debug('Args: %s', args)

    if not args.test_client:
        # Start Running Loop:
        logger.info('Starting ' + AppName + ' System')
        Running = True
        while Running:
            instance = None

            try:
                #if (is_changed(GCClient)):
                #    reload(GCClient)

                instance = GCClient(debug=args.debug,
                                    version=Version,
                                    enable_comms=args.disable_comms,
                                    config_file=args.conf,
                                    client_id=args.client_id,
                                    gc_amqp_host=args.amqp_host,
                                    gc_amqp_port=args.amqp_port,
                                    gc_amqp_sslon=args.amqp_ssl_on)

                while instance.isRunning():
                    time.sleep(30)
            except KeyboardInterrupt:
                logger.warn('Keyboard Interrupt')
                Running = False
                quit()
            except Exception as e:
                logger.warn('run_client Exception Occured!!', exc_info=True)
            finally:
                logger.warn('run_client starting finally statement')

                if instance is not None:
                    instance.quit()

                logger.warn('Reloading Client in 10sec')
                time.sleep(10)
    else:
        instance = GCClient(debug=args.debug,
                            version=Version,
                            enable_comms=args.disable_comms,
                            config_file=args.conf,
                            client_id=args.client_id,
                            gc_amqp_host=args.amqp_host,
                            gc_amqp_port=args.amqp_port,
                            gc_amqp_sslon=args.amqp_ssl_on)
        taskObj = {}
        command = {}
        #queue_object = DeferredQueue()

        taskObj['TaskId'] = 'ABC123'
        taskObj['routingKey'] = 'GREYUNI.GREYTEST'
        taskObj[GC_Utility.GC_TASKREF] = 'Ref123'

        taskObj[GC_Utility.GC_CMD_DATA] = {}

        taskObj[GC_Utility.GC_MODULEID] = 'selenium'
        taskObj[GC_Utility.GC_CMD_DATA]['cmd'] = 'execute_url'
        taskObj[GC_Utility.GC_CMD_DATA]['timer'] = 10

        #queue_object.put(['ch','method','properties',json.dumps(taskObj).encode()])
        url_list = ['http://www.cnn.com',
                    'https://www.starwars.com',
                    'https://www.pacom.mil/staff/staff-J4.htm',
'http://www.c7f.navy.mil/news/2006/november/061112-N-8487G-092-l.jpg',
'https://www.nintendo.co.jp/n02/dmg/acxj/master6.gif',
'http://www.nintendo.co.jp/n01/n64/software/nus_p_nalj/smash/flash/0201/level_x/221_x.jpg',
'http://www.nintendo.co.jp/n01/n64/software/nus_p_nk4j/gallery/tenzi04/1232.jpg',
'http://www.nellis.af.mil/shared/images/val/80463465689.gif',
'http://www.wikipedia.org/art/k/w.html',
'http://www.tradoc.army.mil/tadlp/documents/DTFM Training SOP 17Oct00[1].htm',
'http://www.swrt.co.uk/221777.html',
'http://www.nintendo.co.jp/n08/aa2j/b_naiyou.gif',
'http://www.nintendo.co.jp/n01/n64/software/nus_p_nk4j/gallery/tenzi04/1475.jpg',
'http://www.nintendo.co.jp/n08/atoj/chara/img_12.gif',
'http://www.buckley.af.mil/news/story.asp_storyID=123047290.html',
'https://www.wikipedia.org/img/n/q/3.jpg',
'http://www.pacom.mil/news/news2003/0308JTF519.pdf',
'https://www.starwars.com/community/askjc/nick/askjc20001009.html',
'https://www.wikipedia.org/img/n/o/s.jpg',
'https://www.aviano.af.mil/photos/media_email.asp_id=102961.html',
'https://www.caida.org/publications/bib/networking/entries/griffin02on.xinc',
'http://www.nintendo.co.jp/n01/n64/software/nus_p_nk4j/gallery/tenzi/0139.gif'
]

        for url in url_list:
          taskObj[GC_Utility.GC_CMD_DATA]['url'] = url
          instance.logging_callback('ch','method','properties',json.dumps(taskObj).encode())
          time.sleep(5)

        time.sleep(180)
        instance.quit()
# Execute Main:
if __name__ == "__main__":
    main(sys.argv)
