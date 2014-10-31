from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor

clientchosen = 0
cmdstate = 0
filename = ''
filedata = ''
'''
cmdstate 1: text transfer
cmdstate 2: get file
cmdstate 3: send file

msgend001 : Message sent normally
msgend002 : Error occurred
msgend003 : Indicator for receiving data
msgend004 : Indicator for finished receiving
'''
#------------------------------------------------------------------------------------------------------CLIENTS CONNECTED TO SERVER
def listclients(self):
    for item in self.factory.clients:
        print "Clients: "+ str(item.transport.getPeer())
    print '\n'
#------------------------------------------------------------------------------------------------------SEND CMD TO CLIENT
def writeclient(self): #taking input and sending it to client
    global clientchosen
    global cmdstate
    global filename

    cmd = raw_input()
    if cmd.lower() == "exit":
        listclients()
        clientchosen = input('Choose client number: ')
        writeclient(self)
    elif cmd[:3].lower() == "get":
        cmdstate = 2
        filename = cmd[4:]
        self.factory.clients[clientchosen].transport.write(cmd)
    elif cmd[:4].lower() == "send":
        cmdstate = 3
        filename = cmd[5:]
        self.factory.clients[clientchosen].transport.write(cmd)
    else:
        cmdstate = 1
        self.factory.clients[clientchosen].transport.write(cmd)
#------------------------------------------------------------------------------------------------------STATE AND REACTION
def interactfunc(state, self):
    global clientchosen
    if state == "connMade":
        clientchosen = input('Choose client number: ')
        writeclient(self)

    if state == "connLost":
        clientchosen = input('Choose client number: ')
        writeclient(self)

    if state == "dataRecv":
        writeclient(self)
#------------------------------------------------------------------------------------------------------PROTOCOLS

class SCC_Comms(Protocol):
    def connectionMade(self):
        self.factory.clients.append(self)

        listclients(self)
        interactfunc("connMade", self)

    def connectionLost(self, reason):
    	print "Lost Client: "+ str(self.transport.getPeer())
        self.factory.clients.remove(self)

        listclients(self)
        interactfunc("connLost", self)

    def dataReceived(self, data):
        global cmdstate
        global filename
        global filedata
        #----------------------------------------------------------------------------------------------FROM CLIENT CMD PROMPT
        if cmdstate == 1: #text transfer
            if 'msgend001' in data: #end of message
                print data[:-9], #remove last 9 chars: msgend001
                interactfunc("dataRecv", self)
            else:  
                print data,
        #----------------------------------------------------------------------------------------------FILE FROM CLIENT PC
        elif cmdstate == 2: #get file
            if 'msgend001' in data: #end of message
                filedata += data[:-9]
                with open(filename, 'wb') as f:
                    f.write(filedata) #remove last 9 chars: msgend001
                filedata = ''
                print 'File has been received.\n>',
                interactfunc("dataRecv", self)

            elif 'msgend002' in data: #errormsg
                print 'Error: '+data[:-9]

            else:  
                filedata += data
        #----------------------------------------------------------------------------------------------FILE SENT TO CLIENT PC
        elif cmdstate == 3: #send file
            if 'msgend003' in data: #end of message
                filebytes = ''
                with open(filename, "rb") as f:
                    filebytes += f.read()
                self.factory.clients[clientchosen].transport.write(filebytes)
                self.factory.clients[clientchosen].transport.write('msgend001')
                print 'File has been sent.\n>',
            elif 'msgend004' in data:
                interactfunc("dataRecv", self)
#------------------------------------------------------------------------------------------------------

factory = Factory()
factory.protocol = SCC_Comms
factory.clients = []

reactor.listenTCP(2881, factory)
print "Server Started\n"
reactor.run()