# Command list
#
# Client -> Server
# JOIN nickname - Join to server
# NICK nickname - Change nickname
# MSGS message - Send a message to server
# QUIT          - Disconnect
# SUBC          - Subsribe to receive messages
# SUBO          - Disable subscription
# CHNL          - Switch to channel
# CHDC          - Disconnect from a channel
# USRS          - Show users on the channel
# CHLS          - Show a list of channels


# Server -> Client
# WLCM serverinfo - Welcome message after JOIN
# INFO information - Any info to client
# STOP reason      - Information that connection closed by the server
# MSGR message    - User message relayed from server
# RECV            - Message was received
# RQIT              - Quit message received

# Message is what gets sent over TCP
class Message:
    def __init__(self, type, payload):
        self.type = type
        self.payload = payload

    def packet(self):
        message = self.type+" "+self.payload
        return message.encode()

# Command is what is received through TCP
# Helper class to help parsing
class IncomingMessage:
    # raw_message is the raw packet received
    def __init__(self, raw_message):
        message = raw_message.decode()
        self.length = len(message)

        # expecting that the first 4 characters are the command
        self.type = message[:4]

        # rest of the message is body
        self.payload = message[5:]
