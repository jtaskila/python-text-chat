import server.server as server

def main():
    service = server.Server()
    service.log("Server is starting")
    service.io()

if __name__ == '__main__':
    main()
