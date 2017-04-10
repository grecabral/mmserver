from config import *
from server_config import *
import logging
import socket
import sys
from thread import *
from time import time


class clientWorker:
    def __init__(self, clientSock):
        self.clientSock = clientSock
        self.pingAvgMS = -1
        self.localIP = ""

        # Get peer name of client(external ip)
        clientTuple = clientSock.getpeername()
        self.externalIP = clientTuple[0]
        self.externalPort = clientTuple[1]
        self.str = "{0}:{1}".format(self.externalIP, self.externalPort)
        self.clientLogger = logging.getLogger("{0}".format(self.str))
        start_new_thread(self.mainLoop ,())

    def __str__(self):
        return self.str

    def __unicode__(self):
        return unicode(self.str)


    def pingLoop(self):
        # Initializing variables for ping measurement
        s_time = []
        r_time = []
        s_qt = 0
        r_qt = 0

        # Sending first ping
        s_time.append(time())
        self.clientLogger.warning('Sending ping({0})'.format(s_qt))
        self.clientSock.sendall(MSG_PING)
        s_qt += 1

        # Ping Loop, waits for user to ping back, counts the time and then send another ping
        self.clientLogger.warning(PING_LOOP)
        while True:

            try:
                data = self.clientSock.recv(BUFF)
                
                # Checks if received message is Ping and count it
                if MSG_QUIT in data or not data: 
                    self.clientSock.sendall(MSG_DC)
                    self.clientLogger.warning("PingLoop - Empty data or msg quit")
                    break
                self.clientLogger.warning("{}({})".format(data,len(data)))

                if MSG_PING in data:                
                    self.clientLogger.warning('Received ping({0})'.format(r_qt)) 
                    r_time.append(time())
                    r_qt += 1

                # Checks if there was enough pings
                if r_qt == PING_QT:
                    # Calculate average ping
                    pingAvg = 0
                    for x in xrange(0, PING_QT):
                        pingAvg += r_time[x] - s_time[x]
                    pingAvg /= PING_QT
                    self.pingAvgMS = int(round(pingAvg*1000))
                    self.clientLogger.warning("Average ping = {0}s = {1}ms".format(pingAvg, self.pingAvgMS))
                    break

                # Checks if it can send another ping
                if s_qt < PING_QT:
                    s_time.append(time())
                    self.clientLogger.warning('Sending ping({0})'.format(s_qt)) 
                    self.clientSock.sendall(MSG_PING)
                    s_qt += 1
            except socket.error:
                # If the client disconnected with an error
                self.clientLogger.warning("Forced Disconnection!")
                break

    def localIpLoop(self):
        self.clientLogger.warning("Sending Local IP Message")
        self.clientSock.sendall(MSG_LOCALIP)
        self.clientLogger.warning(LOCALIP_LOOP)
        while True:
            try:
                data = self.clientSock.recv(BUFF)
                
                if MSG_QUIT in data or not data: 
                    self.clientSock.sendall(MSG_DC)
                    self.clientLogger.warning("LocalIPLoop - Empty data or msg quit")
                    break

                
                self.clientLogger.warning("{}({})".format(data,len(data)))
                if MSG_LOCALIP in data:
                        ip = data.split()[1]
                        self.localIP = ip
                        self.clientLogger.warning(data)

                        self.clientLogger.warning("Senging done message")
                        self.clientSock.sendall("{} - {} = {}ms".format(MSG_DONE,MSG_PING_RESULT, self.pingAvgMS))
                        break
            except socket.error:
                # If the client disconnected with an error
                self.clientLogger.warning("Forced Disconnection!")
                break


    def mainLoop(self):
        # Creates logger for the client messages   
        self.pingLoop()
        
        self.localIpLoop()

        # Client listener main loop
        self.clientLogger.warning(MAIN_LOOP)
        self.clientSock.sendall('Welcome to the server. Type something and hit enter\n')

        while True:
            # Receiving from client
            try:
                data = self.clientSock.recv(BUFF)
                self.clientLogger.warning("{}({})".format(data,len(data)))
                reply = 'I dont know this command = ' + data

                # Breaks if received data is quit or none
                if MSG_QUIT in data or not data: 
                    self.clientSock.sendall(MSG_DC)
                    self.clientLogger.warning("MainLoop - Empty data or msg quit")
                    break

                if MSG_LOCALIP in data:
                    self.clientLogger.warning("LocalIP Response = {}".format(data))

                # TO-DO
                # Refreshes ping
                if MSG_PING in data:
                    self.pingLoop()

                # If the client wants to connect to a game
                if MSG_CONNECT in data:
                    self.clientLogger.warning("Searching for the best player to match")

                    # Remove self from the list of players to search

                    bestMatch = None

                    # Search for the best ping in the list of players
                    for ip, p_array in players.iteritems():
                        for op in p_array:
                            if op != self:
                                if not bestMatch:
                                    bestMatch = op
                                else:
                                    if op.pingAvgMS < bestMatch.pingAvgMS:
                                        bestMatch = op

                    # If there is a player trying to connect
                    if bestMatch:
                        self.clientLogger.warning("Found best match")
                        hostMessage = "{}".format(MSG_HOST)
                        
                        # If the other player's ping is better then this client's
                        if bestMatch.pingAvgMS < self.pingAvgMS:
                            self.clientLogger.warning("Client")
                            # Sends a message to this clients saying that he will be the client
                            if bestMatch.externalIP != self.externalIP:
                                clientMessage = "{}-{}".format(MSG_CLIENT, bestMatch.externalIP)
                            else:
                                clientMessage = "{}-{}".format(MSG_CLIENT, bestMatch.localIP)
                            reply = clientMessage
                            # Sends a message to the other client saying he will be the host
                            bestMatch.clientSock.sendall(hostMessage)
                        
                        else:
                            # else do the oposite
                            self.clientLogger.warning("Host")
                            if bestMatch.externalIP != self.externalIP:
                                clientMessage = "{}-{}".format(MSG_CLIENT, self.externalIP)
                            else:
                                clientMessage = "{}-{}".format(MSG_CLIENT, self.localIP)
                            reply = hostMessage
                            bestMatch.clientSock.sendall(clientMessage)                   
                    else:
                        # In case no other player is trying to play online
                        self.clientLogger.warning("No match found")
                        reply = MSG_NONEFOUND

                # If the client sends a request for the list of players
                if MSG_LISTPLAYERS in data:
                    self.clientLogger.warning("Listing players to {}".format(self.str))

                    # Create a list of players without the client
                    otherPlayers = list(players)
                    otherPlayers.remove(self)

                    # If there are players connected to the server
                    if otherPlayers:
                        reply = "{} = \n".format(MSG_LISTPLAYERS)

                        # Adds the player and his ping to the list
                        for op in otherPlayers:
                            reply += "{} - ({}ms)\n".format(op.str, op.pingAvgMS)
                    else:
                        reply = MSG_NONEFOUND

                # Sends the answer to the client
                self.clientSock.sendall(reply)
            except socket.error:
                # If the client disconnected with an error
                self.clientLogger.warning("Forced Disconnection!")
                break

         
        # Came out of loop, log closed connection, remove from list and closes socket
        logger.warning("{0} - Closed Connection".format(self))
        removeClient(self)
        self.clientSock.close()

# Basic logging config
logging.basicConfig(format='%(asctime)s - %(name)s > %(message)s', level=logging.DEBUG)

# Players list init
players = {}

# Add client to list
def addClient(clientWorker):
    externalIP = clientWorker.externalIP
    if externalIP not in players:
        players[externalIP] = []
    players[externalIP].append(clientWorker)
    listClients()

# Remove client from list
def removeClient(clientWorker):
    externalIP = clientWorker.externalIP
    if externalIP in players:
        for p in players[externalIP]:
            if p == clientWorker:
                players[externalIP].remove(p)
                if not len(players[externalIP]):
                    players.pop(externalIP, None)
    listClients()

# List clients on list
def listClients():
    # Default text if there are no clients connected
    text = "No players connected"
    # Check list's size
    if len(players):
        # Change default text and append each client in the text
        text = "Players connected:"
        for ip, p_array in players.iteritems():
            for p in p_array:
                t_ping = "Not measured yet"
                if p.pingAvgMS != -1:
                    t_ping = "{}ms".format(p.pingAvgMS)
                text += "\n{} ({})".format(p, t_ping)
    # Log text
    logger.warning(text)

if __name__=='__main__':
    # Sets main logger
    logger = logging.getLogger("{0} v{1}".format(NAME, VERSION))

    for s in sys.argv:
        if PORTCMD in s:
            PORT = int(s[len(PORTCMD):])
            print 'Argument List:', PORT

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.warning('Socket created') 

    # Bind socket to local host and port
    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        logger.warning('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()

    logger.warning('Socket bind complete on host {0} and port {1}'.format(socket.gethostbyname(socket.gethostname()), PORT))

    # Start listening on socket
    s.listen(10)
    logger.warning('Socket now listening')

    # Function for handling connections. This will be used to create threads

    while True:
        # Wait to accept a connection - blocking call
        clientSock, addr = s.accept()
        logger.warning('Connected with ' + addr[0] + ':' + str(addr[1]))
        # Start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
        # Add client to list if it is new
        client = clientWorker(clientSock)
        addClient(client)
        
         
    s.close()

