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
            '-g',
            '--gap',
            type=int,
            default=None,
            help='Gap between run next task.',
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
        from restfulpy.taskqueue import worker

        signal.signal(signal.SIGINT, self.kill_signal_handler)
        signal.signal(signal.SIGTERM, self.kill_signal_handler)

        if not args.status:
            args.status = {'new'}

        if args.gap is not None:
            settings.worker.merge({'gap': args.gap})

        print(
            f'The following task types would be processed with gap of '
            f'{settings.worker.gap}s:'
        )
        print('Tracking task status(es): %s' % ','.join(args.status))

        number_of_threads = \
            args.number_of_threads or settings.worker.number_of_threads
        for i in range(number_of_threads):
            t = threading.Thread(
                    target=worker,
                    name='restfulpy-worker-thread-%s' % i,
                    daemon=True,
                    kwargs=dict(
                        statuses=args.status,
                        filters=args.filter
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


class CleanupSubSubCommand(SubCommand):
    __command__ = 'cleanup'
    __help__ = 'Clean database before starting worker processes'

    def __call__(self, args):
        from restfulpy.orm import DBSession
        from restfulpy.taskqueue import RestfulpyTask

        RestfulpyTask.cleanup(DBSession, filters=args.filter)
        DBSession.commit()


class WorkerSubCommand(SubCommand):
    __command__ = 'worker'
    __help__ = 'Task queue administration'
    __arguments__ = [
        Argument(
            '-f',
            '--filter',
            default=None,
            type=str,
            action='store',
            help='Custom SQL filter for tasks',
        ),
        StartSubSubCommand,
        CleanupSubSubCommand,
    ]

