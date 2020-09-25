import os, sys
import subprocess
import logging
import time
from datetime import datetime

class UtilStore:
    def __init__(self):
        self.SERVER_SPAM_DELAY = 20 # minimum ssh connection delay in seconds
        self.serverStatus = { 'previousTime' : 0, 'isError' : False, 'message' : 'empty' }

    def verifyEnvironment(self):
        TXT_ENVS = ['SIGNAL_CLI', 'LTO_SSH', 'LTO_LOG_PATH']
        NUM_ENVS = ['WATCH_INTERVAL_MIN', 'MICROBLOCK_DELAY_SEC', 'SSH_CONN_TIMEOUT']
        for env in TXT_ENVS + NUM_ENVS:
            if not env in os.environ or not len(os.environ[env]):
                self.envErr(f'environment variable {env} was not set')
            if self.containsWhiteSpace(os.environ[env]):
                self.envErr(f'environment variable {env} cannot contain white spaces')
        for env in NUM_ENVS:
            try:
                num = int(os.environ[env])
            except ValueError:
                self.envErr(f'{env} must be assigned an integer number')
            if num < 1:
                self.envErr(f'{env} should be a positive integer greater than zero')

    # def launchSignal(self):
    #     logging.info('Launching signal-cli from your PATH...')
    #     proc = subprocess.Popen('signal-cli --singleuser socket'.split(), shell=False)
    #     time.sleep(8)
    #     proc.poll()
    #     if proc.returncode != None:
    #         logging.error(f'signal-cli ended with exit code {proc.returncode}')
    #         sys.exit(1)

    def getDebouncedServerStatus(self):
        now = int(time.time())
        if now - self.serverStatus['previousTime'] < self.SERVER_SPAM_DELAY:
            return self.serverStatus
        logging.debug('*** Requesting crypto server status')
        self.serverStatus['previousTime'] = now
        exitcode, serverLines = self.getOutputFromLTOServer()
        if exitcode != 0:
            self.serverStatus['isError'] = True
            self.serverStatus['message'] = 'cannot connect to server!'
            return self.serverStatus
        microblockDelay = self.getMicroblockDelay(serverLines)
        if microblockDelay > int(os.environ['MICROBLOCK_DELAY_SEC']):
            self.serverStatus['isError'] = True
            self.serverStatus['message'] = f'MicroBlock delay is {microblockDelay} seconds, mining software crashed?'
            return self.serverStatus
        self.serverStatus['isError'] = False
        self.serverStatus['message'] = f'OKAY: received healthy MicroBlock delay ({microblockDelay} seconds)'
        return self.serverStatus

    def getOutputFromLTOServer(self):
        host = os.environ['LTO_SSH'].split(':')
        port = host[1]
        if not port: port = 22
        path = os.environ['LTO_LOG_PATH']
        cmds = [
            'ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR '
            f'-o ConnectTimeout={os.environ["SSH_CONN_TIMEOUT"]} -o IdentityFile=~/.config/ltodog/id_ssh '
            f'-p {port} {host[0]} "date +\'%Y-%m-%d %H:%M:%S\' && tac {path} | grep -m1 MicroBlock"']
        proc = subprocess.Popen(' '.join(cmds), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = proc.communicate()
        logging.debug(f'ssh output:\n{output.decode()}')
        if error:
            logging.error(f'ssh error:\n{error.decode()}')
        return proc.returncode, output.decode()

    def getMicroblockDelay(self, serverLines):
        lines = serverLines.split('\n')
        if len(lines) < 2:
            return None
        nowLine, logLine, *other = lines
        try:
            dtObjNow = datetime.strptime(nowLine, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
        try:
            dtObjLog = datetime.strptime(logLine[:19], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
        return int(dtObjNow.timestamp() - dtObjLog.timestamp())

    def prettyPrint(self, commandsList):
        output = []
        for cmd in commandsList:
            aliasList = cmd.split(',')
            line = aliasList[0]
            if len(aliasList) > 1:
                del aliasList[0]
                line += ' (' + ', '.join(aliasList) + ')'
            output.append(line)
        return '\n'.join(output)

    def envErr(self, message):
        logging.error(message)
        sys.exit(1)

    def containsWhiteSpace(self, string):
        for c in string:
            if c.isspace():
                return True
        return False

# EOF
