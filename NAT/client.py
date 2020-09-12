from __future__ import print_function, unicode_literals
from PyInquirer import style_from_dict, Token, prompt, Separator
import sys
import socket
from random import randrange
import pickle
import time
import threading

# Specified style for CLI
style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

# Specified messages for the CLI
messages = [
    {
        'type': 'checkbox',
        'message': 'Please select message type:',
        'name': 'Message type',
        'choices': [
            Separator('= Message types ='),
            {
                'name': 'Ping'
            },
            {
                'name': 'Echo'
            },
            {
                'name': 'Normal message'
            },
            {
                'name': 'Cancel'
            }
        ]
    }
]

# Specified client types for the CLI
client_types = [
    {
        'type': 'checkbox',
        'message': 'Please select client type:',
        'name': 'Client type',
        'choices': [
            Separator('= Client types ='),
            {
                'name': 'Internal'
            },
            {
                'name': 'External'
            },
            {
                'name': 'Quit'
            },
            {
                'name': 'Cancel'
            }
        ]
    }
]

host_ip = ""
host_mac_address = ""

class Client:
    def __init__(self, type, tcp_port, udp_port):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        print_line()
        print("Client: Sending ARP request")

        # ARP Protocol for getting host information
        self.udp_socket.sendto(b'c', ('<broadcast>', udp_port))

        host_info = pickle.loads(self.udp_socket.recv(1024))
        host_ip = host_info[0]
        host_mac_address = host_info[1]

        print("Client: received host ip (%s) and host mac address (%s)" % (host_ip, host_mac_address))

        self.running = True

        # Connect either internal or external clients
        if type == str(0):
            self.connect_external(host_ip, udp_port)
        elif type == str(1):
            self.connect_internal(host_ip, udp_port)


        # Continue to the next option list in CLI
        self.next = False

        # Connect clients to natbox via TCP
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(0.1)
        self.tcp_socket.connect((ip, tcp_port))

        # Start the receiver listener for clients
        receive_thread = threading.Thread(target=self.receive, args=())
        receive_thread.start()

        receiver_ip = ""
        if self.running == True:
            print("If you want to send a message please enter 'send'")

        while(self.running):
            # Enter send to bring up the CLI option menu
            send = input()

            if send == "send":
                while (True):
                    print_line()
                    print("Please choose the type of client:")
                    print_line()

                    # Prompt the client choices
                    client_choice = prompt(client_types, style=style)

                    # Build a list of the client choices (PyInquerier works with 2D dictionaries, this makes it easier)
                    list = []
                    for i in client_choice.values():
                        list.append(i)

                    try:
                        if len(list[0]) > 1:
                            print("Please only select one client type.")
                            print_line()

                        elif len(list[0]) == 1:
                            if list[0][0] == "Internal":
                                print("Please enter the ip as follows: <ip>:<port>")

                                receiver_ip = input()
                                self.next = True

                                break

                            elif list[0][0] == "External":
                                print("Please enter the ip as follows: <ip>")

                                receiver_ip = input()
                                self.next = True

                                break

                            elif list[0][0] == "Cancel":
                                print("If you want to send a message please enter 'send'")

                                self.next = False

                                break

                            elif list[0][0] == "Quit":
                                print("Client: Quiting")
                                print_line()

                                msg = (self.client_ip + ':quit').encode('utf-8')
                                self.tcp_socket.send(msg)
                                self.next = False
                                self.running = False

                                break
                    except:
                        print("Please choose a client type.")
                        print_line()

                while (self.next):
                    x = receiver_ip.split(":")

                    print_line()

                    # Prompt message types for CLI
                    answers = prompt(messages, style=style)

                    # Build a list of message types
                    list = []
                    for i in answers.values():
                        list.append(i)

                    try:
                        if len(list[0]) > 1:
                            print("Please only select one message type.")
                            print_line()

                        elif len(list[0]) == 1:
                            if list[0][0] == "Ping":

                                if len(x) == 1:
                                    print("Client: Sending ping to ip %s." % (x[0]))
                                    print_line()

                                    self.send_pacquet(x[0], "8-0")

                                elif len(x) == 2:
                                    ip_to = x[0] + ":" + x[1]

                                    print("Client: Sending ping to ip %s." % (ip_to))
                                    print_line()

                                    self.send_pacquet(ip_to, "8-0")

                                break

                            elif list[0][0] == "Echo":
                                print("Client: Please enter the message you want to send.")
                                message = input()

                                if len(x) == 1:
                                    print("Client: Echoing ip %s." % (x[0]))
                                    print_line()

                                    msg = "-echo:" + message
                                    self.send_pacquet(x[0], msg)

                                elif len(x) == 2:
                                    ip_to = x[0] + ":" + x[1]

                                    print("Client: Echoing ip %s." % (ip_to))
                                    print_line()

                                    msg = "-echo:" + message
                                    self.send_pacquet(ip_to, msg)

                                break

                            elif list[0][0] == "Normal message":
                                print("Client: Please enter the message you want to send.")
                                message = input()

                                if len(x) == 1:
                                    print("Client: Sending message to ip %s." % (x[0]))
                                    print_line()

                                    self.send_pacquet(x[0], message)

                                elif len(x) == 2:
                                    ip_to = x[0] + ":" + x[1]

                                    print("Client: Sending message to ip %s." % (ip_to))
                                    print_line()

                                    self.send_pacquet(ip_to, message)

                                break

                            elif list[0][0] == "Cancel":
                                break
                    except:
                        print("Please choose a message type.")

    def receive(self):
        while (self.running):
            msg = self.tcp_socket.recv(1024)

            if msg == b'':
                continue

            msg = msg.decode('utf-8')
            msg = msg.split(":")

            if msg[0] == str(12) and msg[1] == str(2):
                print("Error, bad IP length")

            elif msg[0] == str(12) and msg[1] == str(1):
                print("Error, missing arguments")

            else:
                if len(msg) == 3:
                    ip_to = msg[0] + ":" + msg[1]

                    if "#Ping!" in msg:
                        self.send_pacquet(ip_to, "0-0")

                        print(msg[0] + ":" + msg[1] + ": " + msg[2][1:])

                    elif "-echo" in msg[2]:
                        echo_msg = msg[2][5:]

                        self.send_pacquet(ip_to, echo_msg)

                        print(msg[0] + ":" + msg[1] + ": " + echo_msg)

                    else:
                        if "#Ping!" not in msg:
                            if msg[2] == "3-1":
                                print(msg[0] + ":" + msg[1] + ": External client not reachable.")

                            elif msg[2] == "3-3":
                                print(msg[0] + ":" + msg[1] + ": Internal client not reachable.")

                            else:
                                print(msg[0] + ":" + msg[1] + ": " + msg[2])

                else:
                    ip_to = msg[0]

                    if "#Ping!" in msg:
                        self.send_pacquet(ip_to, "0-0")

                        print(msg[0] + ": " + msg[1][1:])

                    elif "-echo" in msg[1]:
                        echo_msg = msg[1][5:]

                        self.send_pacquet(ip_to, echo_msg)

                        print(msg[0] + ": " + echo_msg)

                    else:
                        if "#Ping!" not in msg:
                            if msg[1] == "3-1":
                                print(msg[0] + ": External client not reachable.")
                            elif msg[1] == "3-3":
                                print(msg[0] + ": Internal client not reachable.")
                            else:
                                print(msg[0] + ": " + msg[1])

    def build_pacquet(self, to, message):
        pacquet = self.client_ip + ":" + to + ":" + message
        return pacquet

    def send_pacquet(self, ip_to, msg):
        pacquet = self.build_pacquet(ip_to, msg)
        self.tcp_socket.send(pacquet.encode('utf-8'))

    def disconnect(self, ip, udp_port):
        msg = ('x' + self.client_ip).encode('utf-8')

        self.udp_socket.sendto(msg, (ip, udp_port))

        self.udp_socket.close()
        self.tcp_socket.close()

    def connect_internal(self, ip, udp_port):

        self.udp_socket.sendto("d".encode('utf-8'), (ip, udp_port))

        print("Client: Discover sent")

        time.sleep(0.1)
        new_ip = self.udp_socket.recv(1024)

        print("Client: Received reply from server")

        if new_ip.decode('utf-8') == "e":
            self.running = False
            self.next = False

            self.udp_socket.close()

            print("Client: Failed to connect ( The pool is empty )")

        else:
            self.get_mac()

            print("Client: Assigned MAC address: ", self.mac)

            new_ip = new_ip.decode('utf-8')
            self.client_ip = new_ip

            print("Client: Received ip from pool: ", new_ip)

            # Send request to natbox
            req = "r" + str(self.client_ip) + ":" + self.mac
            self.udp_socket.sendto(req.encode('utf-8'), (ip, udp_port))

            print("Client: Sending request for IP: ", self.client_ip)

            # Receive acknowledgement from natbox
            a = self.udp_socket.recv(1024)

            print("Client: Client connected to natbox on ip: ", self.client_ip)
            print_line()

    def connect_external(self, ip, udp_port):
        self.get_mac()

        print("Client: Assigned MAC address: ", self.mac)

        while (True):
            new_ip = "212.30." + str(randrange(256)) + "." + str(randrange(256))

            msg = "e" + str(new_ip) + ":" + self.mac
            msg = msg.encode('utf-8')

            self.udp_socket.sendto(msg, (ip, udp_port))

            time.sleep(0.1)
            try:
                reply = self.udp_socket.recv(1024).decode('utf-8')
            except:
                reply = ""
                pass

            if reply == "a":
                self.client_ip = new_ip

                print("Client: External client connected on ip, ", new_ip)
                print_line()
                break

    def get_mac(self):
        while (True):
            mac = "%02x:%02x:%02x:%02x:%02x:%02x" % (randrange(255), randrange(255),
                                                     randrange(255), randrange(255),
                                                     randrange(255), randrange(255))

            mac_str = ("mac" + mac).encode('utf-8')
            self.udp_socket.sendto(mac_str, (ip, udp_port))
            time.sleep(0.1)
            msg = self.udp_socket.recv(1024)
            try:
                msg = msg.decode('utf-8')
            except:
                msg = ""
            time.sleep(0.1)

            if msg == "a":
                self.mac = mac
                break


def print_line():
    print("########################################################################################")


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if __name__ == '__main__':
    tcp_port = 8001
<<<<<<< HEAD
    udp_port = 5001
=======
    udp_port = 6968
>>>>>>> 4cf98e3fa5748083a31d363b866ac8eddda42ddd
    type = sys.argv[1]

    ip = get_ip()

    Client(type, tcp_port, udp_port)
