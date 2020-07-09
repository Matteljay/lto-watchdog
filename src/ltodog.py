#!/usr/bin/python3
import logging
import sys
import signal # for SIGINT, SIGHUP (https://unix.stackexchange.com/a/251267)
import time

from UtilStore import UtilStore
from SignalHook import SignalHook
from Commander import Commander
from Watcher import Watcher

def sigHandler(signal, frame):
    logging.info(f'Clean exit, received signal {signal}')
    sys.exit(0)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        datefmt='%Y-%m-%dT%H:%M:%S',
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    signal.signal(signal.SIGINT, sigHandler)
    signal.signal(signal.SIGTERM, sigHandler)
    signal.signal(signal.SIGHUP, sigHandler)

    store = UtilStore()
    store.verifyEnvironment()
    #store.launchSignal()
    signalHook = SignalHook()
    signalHook.connect()
    commander = Commander(store, signalHook)
    commander.loadAccountsFile()
    watcher = Watcher(store, commander)
    while True:
        if signalHook.receive():
            commander.handleMessages()
            watcher.worker()
            time.sleep(1)
        else:
            signalHook.connect()

# EOF
