import threading
import socket
import server.messages as messages
import random

class Server:
    def __init__(self):
        # initializing the server
        self.running = True
        self.host = '127.0.0.1'
        self.port = 59392
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
        except socket.error:
            self.server.log("Could not bind socket")

        # server buffers
        self.clients = list() # list of clients

        # thread for accepting connections
        self.connectionListener = ConnectionListener(self)
        self.connectionListener.start()

    # server logger
    # output to std or whatever
    def log(self, message):
        print(str(message))

    # server commands
    def io(self):
        while(self.running):
            command = input("Server command: ")
            if command == "exit":
                self.running = False
                self.push_socket()

    # add message to every clients queue
    def addToQueue(self, message, channel = "all"):
        for client in self.clients:
            if channel == "all":
                client.addToQueue(message)
            else:
                if client.channel == channel:
                    client.addToQueue(message)

    # connect to the waiting socket so it can be closed
    def push_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.close()

class ConnectionListener(threading.Thread):
    def __init__(self, server):
        super().__init__()
        self.server = server #handle to parent server class

    def run(self):
        while(self.server.running):
            connection, address = self.server.socket.accept()
            self.server.log("A client has connected")
            self.server.clients.append(ClientHandler(self.server, connection, address))

        # closing the socket on exit
        self.server.socket.close()

# class handles both incoming and outgoing threads
class ClientHandler:
    def __init__(self, server, connection, address):
        self.server = server     # handle to the server class
        self.socket = connection # handle to the client socket
        self.address = address
        self.messageQueue = list() # messagequeue for clientsender

        self.nickname = "user_"+str(random.randint(10000,99999))
        self.subscription = True
        self.channel = None

        self.reader = ClientReader(self)
        self.reader.start()

        self.sender = ClientSender(self)
        self.sender.start()

    def addToQueue(self, message):
        self.messageQueue.append(message)

# handles all messages sent to client
class ClientSender(threading.Thread):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        while(self.client.server.running):
            for message in self.client.messageQueue:
                try:
                    if self.client.subscription == True and self.client.channel != None:
                        self.client.socket.sendall(message.packet())
                    else:
                        if message.type == "INFO" or message.type == "WLCM":
                            self.client.socket.sendall(message.packet())

                    self.client.messageQueue.remove(message)
                except socket.error:
                    break

# handles all messages coming from the client
class ClientReader(threading.Thread):
    def __init__(self, client):
        self.client = client
        super().__init__()

    def run(self):
        while(self.client.server.running):
            try:
                message = self.client.socket.recv(1024)
            except socket.error:
                break

            incomingMessage = messages.IncomingMessage(message)

            if incomingMessage.type == "MSGS":
                # if a client is not in a channel, don't send its messages
                if self.client.channel != None:
                    self.client.server.addToQueue(messages.Message("MSGR", "<"+self.client.nickname+"@"+str(self.client.channel)+"> "+incomingMessage.payload), self.client.channel)
                else:
                    self.client.addToQueue(messages.Message("INFO", "Join to a channel before you can post messages!"))

            if incomingMessage.type == "CHNL":
                self.client.channel = incomingMessage.payload
                self.client.addToQueue(messages.Message("INFO", "You are now talking on channel: "+incomingMessage.payload))
                self.client.server.addToQueue(messages.Message("INFO", self.client.nickname+" joined the channel!"), str(self.client.channel))

            if incomingMessage.type == "CHDC":
                self.client.server.addToQueue(messages.Message("INFO", self.client.nickname+" left the channel."), str(self.client.channel))
                self.client.addToQueue(messages.Message("INFO", "You have disconnected from channel: "+str(self.client.channel)))
                self.client.channel = None

            if incomingMessage.type == "CHLS":
                channels = list()
                for sClient in self.client.server.clients:
                    if sClient.channel not in channels and sClient.channel != None:
                        channels.append(sClient.channel)
                channel_string = ", ".join(channels)
                self.client.addToQueue(messages.Message("INFO", "Available channels: "+channel_string))

            if incomingMessage.type == "USRS":
                if self.client.channel != None:
                    users = list()
                    for sClient in self.client.server.clients:
                        if sClient.channel == self.client.channel:
                            users.append(sClient.nickname)
                            users_string = ", ".join(users)
                    self.client.addToQueue(messages.Message("INFO", "Users on channel: "+users_string))
                else:
                    self.client.addToQueue(messages.Message("INFO", "You are not in any channel"))

            if incomingMessage.type == "JOIN":
                self.client.addToQueue(messages.Message("WLCM", "Welcome to the chat!"))

            if incomingMessage.type == "NICK":
                self.client.server.addToQueue(messages.Message("INFO", self.client.nickname+" is now known as "+incomingMessage.payload))
                self.client.nickname = incomingMessage.payload

            if incomingMessage.type == "SUBC":
                self.client.subscription = True
                self.client.addToQueue(messages.Message("INFO", "You are now receiving messages"))

            if incomingMessage.type == "SUBO":
                self.client.subscription = False
                self.client.addToQueue(messages.Message("INFO", "Messages disabled"))

            if incomingMessage.type == "QUIT":
                self.client.addToQueue(messages.Message("RQIT", ""))
                break

            self.client.server.log("<"+str(self.client.address)+"> "+message.decode())

        # clean up after client disconnecting
        self.client.running = False
        self.client.socket.close()
        self.client.server.clients.remove(self.client)
        self.client.server.addToQueue(messages.Message("INFO", self.client.nickname+" has left."))
        self.client.server.log(self.client.nickname+" dropped")
