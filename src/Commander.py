import logging
import json
import os

class Commander:
    def __init__(self, store, signalHook):
        self.ACCOUNTS_FILE = os.path.expanduser('~/.config/ltodog/contacts.json')
        self.COMMANDS = [
            'help,h,list',
            'unsubscribe,unsub',
            'contacts,cont,subs',
            'trustall',
            'status,stat,st']
        self.WELCOME = 'Welcome, you are now subscribed to the LTO watchdog and will receive messages when crypto connectivity is lost. Type \'help\' for a list of commands'
        self.store = store
        self.signalHook = signalHook
        self.contactDict = {}

    def loadAccountsFile(self):
        try:
            with open(self.ACCOUNTS_FILE, 'r+') as fd:
                self.contactDict = json.load(fd)
            logging.info('Loaded accounts from file: ' + self.ACCOUNTS_FILE)
        except FileNotFoundError:
            logging.info('Could not yet read from file: ' + self.ACCOUNTS_FILE)

    def writeAccountsFile(self):
        try:
            os.makedirs(os.path.dirname(self.ACCOUNTS_FILE), exist_ok=True)
            with open(self.ACCOUNTS_FILE, 'w') as fd:
                json.dump(self.contactDict, fd)
            logging.debug('Wrote to accounts file: ' + self.ACCOUNTS_FILE)
        except Exception as e:
            logging.error(e)

    def sendMessageSubscribed(self, message):
        subs = self.getAllSubscribed()
        if subs:
            logging.info('SENDING: ' + message)
            sendObject = { 'sendMessage': { 'contacts' : subs, 'message' : message } }
            self.signalHook.send(json.dumps(sendObject))
    
    def getAllSubscribed(self):
        subscribed = []
        for k, v in self.contactDict.items():
            if 'subscribed' in v and v['subscribed'] == True:
                subscribed.append(k)
        if not len(subscribed):
            logging.warning('No subscribers found')
        return subscribed

    def handleMessages(self):
        queue = self.signalHook.messageQueue
        while len(queue):
            rawMessage = queue.pop(0)
            logging.debug(rawMessage)
            recvObject = json.loads(rawMessage)
            try:
                self.replyTo = recvObject['envelope']['source']
                msg = recvObject['envelope']['dataMessage']['message']
            except Exception:
                continue
            self.checkWelcome() # any message triggers subscribe action
            self.command = self.matchCmds(msg)
            self.parseCommand()
    
    def checkWelcome(self):
        if self.isSubscribed(self.replyTo):
            return
        self.updateAccount({ 'subscribed' : True })
        self.writeAccountsFile()
        self.replyMsg(self.WELCOME)

    def matchCmds(self, testCmd):
        lowerCmd = testCmd.strip().lower().split()
        if not len(lowerCmd):
            logging.debug(f'ignoring empty command')
            return
        for cmd in self.COMMANDS:
            aliasList = cmd.split(',')
            ret = aliasList[0]
            for alias in aliasList:
                if alias == lowerCmd[0]:
                    return ret
        logging.debug(f'ignoring command: {testCmd}')
        return None

    def parseCommand(self):
        command = self.command
        if command == 'help':
            msg = 'List of commands:\n' + self.store.prettyPrint(self.COMMANDS)
        elif command == 'unsubscribe':
            self.updateAccount({ 'subscribed' : False })
            self.writeAccountsFile()
            msg = 'You were unsubscribed. Send me any message if you want to subscribe again. Bye!'
        elif command == 'contacts':
            msg = 'Subscribed contacts to LTO-dog are:\n' + '\n'.join(self.getAllSubscribed())
        elif command == 'trustall':
            msg = 'NOTICE: all contacts had their keys trusted and sessions updated!'
            subs = self.getAllSubscribed()
            sendObject = { 'trust' : { 'contacts' : subs }, 'endSession' : { 'contacts' : subs },
                'sendMessage': { 'contacts' : subs, 'message' : msg } }
            self.signalHook.send(json.dumps(sendObject))
            return
        elif command == 'status':
            serverStatus = self.store.getDebouncedServerStatus()
            msg = serverStatus['message']
        else:
            return
        self.replyMsg(msg)

    def replyMsg(self, msg):
        sendObject = { 'sendMessage': { 'contacts' : self.replyTo.split(), 'message' : msg } }
        self.signalHook.send(json.dumps(sendObject))

    def updateAccount(self, patchObject):
        number = self.replyTo
        if not number in self.contactDict:
            self.contactDict[number] = patchObject
            return
        self.contactDict[number].update(patchObject)

    def isSubscribed(self, number):
        try:
            return self.contactDict[number]['subscribed'] == True
        except Exception:
            return False

# EOF
