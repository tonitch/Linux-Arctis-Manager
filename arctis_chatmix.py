import logging
import os
import signal
import sys
from typing import Literal

# Setup the notify logging
NOTIFY = 19  # Right before "INFO"
notify_enabled = os.system('which notify-send 1>/dev/null 2>&1') == 0


def logging_notify(self: logging.Logger, summary: str, message: str, urgency: Literal['low', 'normal', 'critical'] = 'normal', *args, **kwargs):
    if notify_enabled:
        args = ['--app-name="Arctis ChatMix"', f'--urgency={urgency}']
        os.system(f'notify-send {' '.join(args)} "{summary}" "{message.format(*args, **kwargs).replace('"', '\\"')}"')
    else:
        self._log(logging.INFO, f'NOTIFICATION: {summary} :: {message}', args, **kwargs)


logging.Logger.notify = logging_notify
# Notify logging end


if __name__ == '__main__':
    import asyncio
    from argparse import ArgumentParser

    from PyQt6.QtWidgets import QApplication
    from qasync import QEventLoop

    from arctis_chatmix.arctis_chatmix_daemon import ArctisChatMixDaemon
    from arctis_chatmix.systray_app import SystrayApp

    args = ArgumentParser()
    args.add_argument('-v', '--verbose', action='count', default=0)
    args = args.parse_args()

    logging.basicConfig(level=logging.CRITICAL, format='%(name)10s %(levelname)8s | %(message)s')

    # Initialize the QApplication here due to the asyncio loop (the app needs to run in the main thread)
    app = QApplication(sys.argv)

    log_level = logging.DEBUG if args.verbose else NOTIFY
    daemon = ArctisChatMixDaemon(log_level=log_level)
    systray_app = SystrayApp(app=app, log_level=log_level)

    def sigterm_handler(sig, frame):
        daemon.stop()
        systray_app.stop()

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    asyncio.ensure_future(systray_app.start())
    asyncio.ensure_future(daemon.start('1.3.1'))

    with event_loop:
        event_loop.run_forever()
