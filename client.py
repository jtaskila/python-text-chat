import threading
import socket
import server.messages as messages

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ClientReader(threading.Thread):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        while(self.client.running):
            try:
                message = self.client.socket.recv(1024)
            except socket.error:
                break

            if message != None:
                incomingMessage = messages.IncomingMessage(message)
                if incomingMessage.type == "MSGR":
                    self.client.output(incomingMessage.payload)
                elif incomingMessage.type == "WLCM":
                        self.client.output(bcolors.OKGREEN+incomingMessage.payload+bcolors.ENDC)
                elif incomingMessage.type=="INFO":
                    self.client.output(bcolors.WARNING+incomingMessage.payload+bcolors.ENDC)
                if incomingMessage.type == "RQIT":
                    self.client.output(incomingMessage.type)
                    break

        self.client.running = False
        self.client.socket.close()

class ClientSender(threading.Thread):
    def __init__(self, client):
        super().__init__()
        self.client = client

    def run(self):
        while(self.client.running):
            for message in self.client.outputQueue:
                try:
                    self.client.socket.sendall(message.packet())
                    self.client.outputQueue.remove(message)
                except socket.error:
                    break
class Client:
    def __init__(self):
        self.running = True

        # buffers
        self.outputQueue = list()
        self.inputQueue = list()

        self.clientReader = ClientReader(self)
        self.clientSender = ClientSender(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.connect(('127.0.0.1', 59392))
        except socket.error:
            print("Unable to connect")
            self.running = False
            return
        self.outputQueue.append(messages.Message("JOIN", ""))

        self.clientReader.start()
        self.clientSender.start()

    def output(self, message):
        print(message)

    def input(self):
        while(self.running):
            message = input("")
            print("\033[A                             \033[A")
            if message == "EXIT" or message == "QUIT":
                self.outputQueue.append(messages.Message("QUIT", ""))
                break
            elif message == "SUBC" or message == "SUBSCRIBE":
                self.outputQueue.append(messages.Message("SUBC", ""))
            elif message == "SUBO" or message == "UNSUBSCRIBE":
                self.outputQueue.append(messages.Message("SUBO", ""))
            elif message == "CHNL" or message == "CHANNEL":
                message = input("Channel to join >> ")
                self.outputQueue.append(messages.Message("CHNL", message))
            elif message == "CHDC" or message == "DISCONNECT":
                self.outputQueue.append(messages.Message("CHDC", ""))
            elif message == "CHLS" or message == "LIST":
                self.outputQueue.append(messages.Message("CHLS", ""))
            elif message == "USRS" or message == "USERS":
                self.outputQueue.append(messages.Message("USRS", ""))
            elif message == "NICK" or message == "NICKNAME":
                message = input("New nickname >> ")
                self.outputQueue.append(messages.Message("NICK", message))
            else:
                self.outputQueue.append(messages.Message("MSGS", message))


if __name__ == '__main__':
    client = Client()
    client.input()
