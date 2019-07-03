import signal
import sys
import threading

from easycli import SubCommand, Argument
from nanohttp import settings


class StartSubSubCommand(SubCommand):
    __command__ = 'start'
    __help__ = 'Starts the background worker.'
    __arguments__ = [
        Argument(
            '-i',
            '--query-interval',
            type=int,
            default=None,
            help='Gap between run next task(secend).',
        ),
        Argument(
            '-s',
            '--status',
            default=[],
            action='append',
            help='Task status to process',
        ),
        Argument(
            '-n',
            '--number-of-threads',
            type=int,
            default=None,
            help='Number of working threads',
        ),
    ]

    def __call__(self, args):
        from restfulpy.mule import worker

        signal.signal(signal.SIGINT, self.kill_signal_handler)
        signal.signal(signal.SIGTERM, self.kill_signal_handler)

        if not args.status:
            args.status = {'new'}

        if args.query_interval is not None:
            settings.jobs.merge({'interval': args.query_interval})

        print(
            f'The following task types would be processed with of interval'
            f'{settings.jobs.interval}s:'
        )
        print('Tracking task status(es): %s' % ','.join(args.status))

        number_of_threads = \
            args.number_of_threads or settings.jobs.number_of_threads
        for i in range(number_of_threads):
            t = threading.Thread(
                    target=worker,
                    name='restfulpy-worker-thread-%s' % i,
                    daemon=True,
                    kwargs=dict(
                        statuses=args.status,
                    )
                )
            t.start()

        print('Worker started with %d threads' % number_of_threads)
        print('Press Ctrl+C to terminate worker')
        signal.pause()

    @staticmethod
    def kill_signal_handler(signal_number, frame):
        print('Terminating')
        sys.stdin.close()
        sys.stderr.close()
        sys.stdout.close()
        sys.exit(signal_number)


class MuleSubCommand(SubCommand):
    __command__ = 'mule'
    __help__ = 'Jobs queue administration'
    __arguments__ = [
        StartSubSubCommand,
    ]

