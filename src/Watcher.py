import logging
import os
from datetime import datetime

class Watcher:
    def __init__(self, store, commander):
        self.store = store
        self.commander = commander
        self.prevWorkMinute = -1
        self.cryptoErrorState = False

    def worker(self):
        nowMinute = datetime.now().minute
        if self.prevWorkMinute == nowMinute:
            logging.debug('Watcher: waiting for the next minute...')
            return
        self.prevWorkMinute = nowMinute
        # Check crypto server frequently
        if self.prevWorkMinute % int(os.environ['WATCH_INTERVAL_MIN']) == 0:
            self.frequentTasks()
        # Possibly other hourly tasks
        #if self.prevWorkMinute == 22:
        #    self.hourlyTasks()

    def frequentTasks(self):
        logging.info(f'frequentTasks triggered {datetime.now().minute}')
        serverStatus = self.store.getDebouncedServerStatus()
        self.communicate(serverStatus['isError'], serverStatus['message'])

    def communicate(self, isError, message):
        if isError:
            logging.error(message)
        else:
            logging.info(message)
        if self.cryptoErrorState != isError:
            self.commander.sendMessageSubscribed(message)
        self.cryptoErrorState = isError

# EOF
