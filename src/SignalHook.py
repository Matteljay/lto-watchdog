import socket
import time
import logging
import os, sys

class SignalHook:
    def __init__(self):
        self.messageQueue = []

    def connect(self):
        try:
            host, portTXT = os.environ['SIGNAL_CLI'].split(':')
            port = int(portTXT)
        except Exception:
            logging.error('bad format for environment variable \'SIGNAL_CLI\', valid example: 127.0.0.1:24250')
            sys.exit(1)
        logging.info(f'Connecting to {host}:{port}...')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.sock.connect((host, port))
                self.sock.setblocking(False) # sock.settimeout(0.0)
                break
            except ConnectionRefusedError:
                logging.info('Refused, attemping to reconnect...')
                time.sleep(3)
        logging.info('Connection established')
        self.initialCommands()
        time.sleep(1)

    def receive(self):
        try:
            buffer = self.sock.recv(65536) # should be plenty for large contact lists
        except BlockingIOError:
            return True
        if not buffer:
            logging.error('Lost connection!')
            return False
        for line in filter(None, buffer.split(b'\n')):
            self.messageQueue.append(line.decode())
        return True

    def send(self, message):
        self.sock.sendall(message.encode() + b'\n')

    def initialCommands(self):
        pass
        #self.send('{ "getContacts" : "" }')
        #self.send('{ "sendMessage" : { "contacts" : [ "+31638555555" ], "groups" : [ "Y5555rtl2p/TnLYvY555dA==", "DK555555UjPU55545557bA==" ], "message" : "This GROUP message comes from Python!" } }')
        #self.send('{ "updateContacts" : { "+31638555555" : { "archived" : false } }, "getContacts" : "" }')
        #self.send('{ "sendMessage" : { "contacts" : [ "+31638555555" ], "message" : "This PM comes from Python <3" } }')
        #self.send('{ "getGroups" : "", "trustAll" : "" }')
        #self.send('{ "endSession" : { "contacts" : [ "+31638555555" ] } }')

# EOF
