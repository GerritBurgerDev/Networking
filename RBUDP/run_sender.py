import sender
import sys


# Run server
def run_server(port):
    sender.run(port)


if __name__ == '__main__':
    server_TCPPort = int(sys.argv[1])  # TCP port
    run_server(server_TCPPort)
