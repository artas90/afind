from __future__ import unicode_literals, print_function
from afind.application import Application


def main():
    import sys
    import signal

    def signal_handler(signal, frame):
        sys.stdout.write('Aborted by pressing Ctrl+C!\n')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    Application().run()


if __name__ == '__main__':
    main()
