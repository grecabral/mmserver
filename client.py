from config import *
from client_config import *
import logging
import socket
import sys
from thread import *

#     time_connection = time()
# Basic logging config
logging.basicConfig(format='%(asctime)s - %(name)s > %(message)s', level=logging.DEBUG)


def pingLoop():
    # Starts Ping Loop
    logger.warning(PING_LOOP)
    while True:
        data = s.recv(BUFF)
        # If data is PING sends the ping back
        if data == MSG_PING:
            logger.warning('Sending Ping')
            s.sendall(MSG_PING)
        # If data is DONE proceed
        if MSG_DONE in data:
            logger.warning('Received Done Message')
            logger.warning(data)
            break

def localIpLoop():
    logger.warning(PING_LOOP)


def chatLoop():
    while True:
        s_data = raw_input ( "SEND( TYPE quit to Quit): " )

        s.send(s_data)


def mainLoop():
    logger.warning(MAIN_LOOP)
    # Client typer
    pingLoop()
    start_new_thread(chatLoop ,())
    while True:
        # Receiving from server
        r_data = s.recv(BUFF)
        server_logger.warning(r_data)

        if r_data == MSG_PING:
            pingLoop()

        # If received a discconect order from the server disconnect
        if r_data == MSG_DC:
            logger.warning('Disconnecting and closing')
            s.close()
            break


if __name__=='__main__':
    # Sets main logger
    logger = logging.getLogger("{0} v{1}".format(NAME, VERSION))

    # Opens socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger.warning('Socket created')
    
    # Try to connect to host
    try:
        s.connect(("162.243.71.157", PORT))
    except socket.error as msg:
        logger.warning('Connection failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()

    serverTuple = s.getpeername()

    logger.warning('Connected with {0} and port {1}'.format(serverTuple[0],serverTuple[1]))

    server_logger = logging.getLogger("{0}:{1}".format(serverTuple[0],serverTuple[1]))
    
    mainLoop()