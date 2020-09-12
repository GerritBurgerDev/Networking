import socket
import re, uuid
import threading
import pickle
import time

pool = []
clients = {}
ext_ips = []
int_ips = []
client_mac_addresses = {}
NAT_Table = {}
NAT_Timer = {}

NAT_time = 30 # seconds

# Initializes sender TCP and UDP sockets
class initializeNAT:
    def __init__(self):
        self.nat_TCPPort = 8001
<<<<<<< HEAD
        self.nat_UDPPort = 5001
=======
        self.nat_UDPPort = 6968
>>>>>>> 4cf98e3fa5748083a31d363b866ac8eddda42ddd
        self.initializeConnection()

    def initializeConnection(self):
        # wait for UDP connection from client
        self.nat_UDPSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
        self.nat_UDPSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.nat_ip, self.nat_mac_address = self.get_host_info()

        print_line()
        print("NATBox info", self.nat_ip, self.nat_mac_address)

        # Open UDP for broadcasts
        self.nat_UDPSocket.bind(('', self.nat_UDPPort))
        self.nat_TCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nat_TCPSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.nat_TCPSocket.bind((self.nat_ip, self.nat_TCPPort))

        print('NATBox: Listening for connections')

        while (True):
            response = self.nat_UDPSocket.recvfrom(1024)

            msg = response[0]
            address = response[1]

            msg = msg.decode('utf-8')
            time.sleep(0.1)

            # Client connects to natbox
            if msg == 'c':
                host_info = [self.nat_ip, self.nat_mac_address]
                host_info = pickle.dumps(host_info)
                self.nat_UDPSocket.sendto(host_info, address)

            #  Receive discover from internal client
            if msg[0] == 'd':
                print("NATBox: Client sent discovery")

                if pool.__len__() == 0:
                    # Tell client the pool is empty
                    self.nat_UDPSocket.sendto(b'e', address)
                    print("NATBox: Client coudl not connect ( pool empty )")

                else:
                    # Send ip from pool
                    msg = pool[0].encode('utf-8')
                    self.nat_UDPSocket.sendto(msg, address)

                    print("NATBox: Sent ip (%s) from pool" % pool[0])

            # Receive request from internal client
            if msg[0] == 'r':
                message = msg.split(":")
                list = message[2:]
                mac_addr = ":"
                mac_addr = mac_addr.join(list)
                ip = message[0] + ":" + message[1]
                ip = ip[1:]

                print("NATBox: Client sent request for ip (%s)" % ip)

                # Remove ip requested from pool
                index = pool.index(ip)
                pool.__delitem__(index)

                print("NATBox: ip (%s) has been remove from pool" % ip)

                # Send an acknowledgement to internal client
                msg = b'a'
                self.nat_UDPSocket.sendto(msg, address)

                client_mac_addresses[mac_addr] = ip

                receive_thread = threading.Thread(target=self.receive, args=(ip,))
                receive_thread.start()

                print("NATBox: Internal client (%s) connected" % ip)
                print_line()

            if msg[:3] == 'mac':
                mac_addr = msg[3:]

                try:
                    ans = client_mac_addresses[mac_addr]

                    # MAC Address already taken
                    msg = b'i'
                    self.nat_UDPSocket.sendto(msg, address)
                except:
                    client_mac_addresses[mac_addr] = ""

                    # Accept MAC address
                    msg = b'a'
                    self.nat_UDPSocket.sendto(msg, address)

            # Connect external client
            if msg[0] == 'e':
                message = msg.split(":")
                list = message[1:]
                mac_addr = ":"
                mac_addr = mac_addr.join(list)
                ip = message[0]
                ip = ip[1:]

                try:
                    ans = ext_ips.index(ip)

                    # Generated external ip already taken
                    msg = b'i'
                    self.nat_UDPSocket.sendto(msg, address)
                except:
                    ext_ips.append(ip)
                    client_mac_addresses[mac_addr] = ip

                    # Accept external ip
                    msg = b'a'
                    self.nat_UDPSocket.sendto(msg, address)

                    receive_thread = threading.Thread(target=self.receive, args=(ip,))
                    receive_thread.start()

                    print("NATBox: External client (%s) connected" % ip)
                    print_line()

    def receive(self, ip):
        self.nat_TCPSocket.listen(1)
        connection_TCPSocket, addr = self.nat_TCPSocket.accept()
        clients[ip] = connection_TCPSocket

        while (True):
            tcp_message = connection_TCPSocket.recv(1024)
            tcp_message = tcp_message.decode('utf-8')

            if tcp_message.__contains__('quit'):
                message = tcp_message.split(":")

                if len(message) == 2:
                    ip_from = message[0]
                elif len(message) == 3:
                    ip_from = message[0] + ":" + message[1]

                head = ip_from[:3]

                if head == "212":
                    mac = ""

                    for key, val in client_mac_addresses.items():
                        if val == ip_from:
                            mac = key

                    client_mac_addresses.__delitem__(mac)
                    index = ext_ips.index(ip_from)
                    ext_ips.__delitem__(index)

                    print("NATBox: Client (%s) has disconnected" % ip_from)

                else:
                    mac = ""

                    for key, val in client_mac_addresses.items():
                        if val == ip_from:
                            mac = key

                    client_mac_addresses.__delitem__(mac)

                    pool.append(ip_from)
                    print("NATBox: Client (%s) has disconnected" % ip_from)

                connection_TCPSocket.close()
                break

            else:
                payload = tcp_message.split(":")
                ip_from = ""
                error = ""

                if payload[0][:3] == "192":
                    if (len(payload[2]) < 7 or len(payload[2]) > 15):
                        ip_to = payload[0] + ":" + payload[1]
                        error = "error12"

                    elif payload[2][:3] != "212" and payload[2][:3] != "192":
                        ip_to = payload[0] + ":" + payload[1]
                        error = "error31"

                    elif payload[2][:3] == "212":
                        if payload[2] not in ext_ips:
                            ip_to = payload[0] + ":" + payload[1]
                            error = "error31"

                    elif payload[2][:3] == "192":
                        ips = ""

                        for ips in int_ips:
                            if payload[1] in ips:
                                ips = "f"

                        if ips == "":
                            ip_to = payload[0] + ":" + payload[1]
                            error = "error31"

                if payload[0][:3] == "212":
                    if (len(payload[1]) < 7 or len(payload[1]) > 15):
                        ip_to = payload[0]
                        error = "error12"

                    elif payload[1][:3] != "212" and payload[1][:3] != "146":
                        ip_to = payload[0]
                        error = "error31"

                    elif payload[1][:3] == "146":
                        port = payload[2]

                        for ips in int_ips:
                            if port in ips:
                                ip_to = ips

                        if ip_to == "":
                            ip_to = payload[0]
                            error = "error31"

                if payload[0][:3] == "192" and payload[2][:3] == "192":
                    if len(payload) < 5:
                        ip_to = payload[0] + ":" + payload[1]
                        error = "error121"

                if payload[0][:3] == "212" and payload[1][:3] == "192":
                    if len(payload) < 4:
                        ip_to = payload[0]
                        error = "error121"

                if payload[0][:3] == "212" and payload[1][:3] == "192":
                    if len(payload) < 4:
                        ip_to = payload[0]
                        error = "error121"

                if error == "error12":
                    dest = clients[ip_to]
                    msg = "12:2"
                    msg = msg.encode('utf-8')
                    dest.send(msg)
                    continue

                if error == "error121":
                    dest = clients[ip_to]
                    msg = "12:1"
                    msg = msg.encode('utf-8')
                    dest.send(msg)
                    continue


                if error == "error31":
                    dest = clients[ip_to]
                    msg = self.nat_ip + ":3-1"
                    msg = msg.encode('utf-8')
                    dest.send(msg)
                    continue

                else:
                    if payload[0][:3] == "192":
                        if payload[2][:3] == "192":
                            ip_from = payload[0] + ":" + payload[1]
                            ip_to = payload[2] + ":" + payload[3]

                            if payload[4] == "8-0":
                                message = "#Ping!"

                            elif payload[4] == "0-0":
                                message = "Pong!"

                            else:
                                if payload[4] == "-echo":
                                    message = payload[4] + payload[5]
                                else:
                                    message = payload[4]
                        else:
                            ip_from = payload[0] + ":" + payload[1]
                            ip_to = payload[2]

                            if payload[3] == "8-0":
                                message = "#Ping!"

                            elif payload[3] == "0-0":
                                message = "Pong!"

                            else:
                                if payload[3] == "-echo":
                                    message = payload[3] + payload[4]
                                else:
                                    message = payload[3]
                    else:
                        if payload[1][:3] == "146":
                            ip_from = payload[0]
                            ip_to = payload[1] + ":" + payload[2]

                            if payload[3] == "8-0":
                                message = "#Ping!"

                            elif payload[3] == "0-0":
                                message = "Pong!"

                            else:
                                if payload[3] == "-echo":
                                    message = payload[3] + payload[4]
                                else:
                                    message = payload[3]
                        else:
                            ip_from = payload[0]
                            ip_to = payload[1]

                            if payload[2] == "8-0":
                                message = "#Ping!"

                            elif payload[2] == "0-0":
                                message = "Pong!"

                            else:
                                message = payload[2]

                if ip_from[:3] == "192" and ip_to[:3] == "192":
                    try:
                        dest = clients[ip_to]

                        msg = str(ip_from) + ":" + message
                        msg = msg.encode('utf-8')

                        dest.send(msg)
                    except:
                        from_dest = clients[ip_from]

                        payload = self.nat_ip + ":" + "3-3"
                        from_dest.send(payload.encode('utf-8'))

                        print("NATBox: Client not found")

                elif ip_from[:3] == "192" and ip_to[:3] == "212":

                    try:
                        dest = clients[ip_to]

                        payload = self.nat_ip + ":" + payload[1] + ":" + message

                        try:
                            dest.send(payload.encode('utf-8'))
                        except:
                            pass

                        if NAT_Table[ip_from] != ip_to:
                            NAT_Table[ip_from] = ip_to
                            timer_thread = threading.Thread(target=self.start_timer, args=(ip_from, NAT_time,))
                            timer_thread.start()
                        else:
                            print("NAT Table entry timer restarted for %s and %s for another 30 seconds" % (ip_from, ip_to))
                            NAT_Timer[ip_from] = NAT_time

                    except:
                        from_dest = clients[ip_from]

                        payload = self.nat_ip + ":3-1"
                        from_dest.send(payload.encode('utf-8'))

                        print("NATBox: Client not found")

                elif ip_from[:3] == "212" and ip_to[:3] == "146":
                    port = ip_to.split(":")
                    ip_to = port[0]

                    if ip_to != self.nat_ip:
                        from_dest = clients[ip_from]

                        payload = self.nat_ip + ":" + "3-3"
                        from_dest.send(payload.encode('utf-8'))

                        print("NATBox: Client not found")

                    else:
                        port = port[1]

                        for x in int_ips:
                            if port in x:
                                ip_to = x

                        try:
                            dest = clients[ip_to]

                            payload = ip_from + ":" + message
                            key = ip_to
                            val = ip_from

                            if NAT_Table[key] != val:
                                NAT_Table[key] = val
                                timer_thread = threading.Thread(target=self.start_timer, args=(ip_from, NAT_time,))
                                timer_thread.start()
                            else:
                                NAT_Timer[ip_from] = NAT_time

                            dest.send(payload.encode('utf-8'))

                        except:
                            from_dest = clients[ip_from]
                            payload = self.nat_ip + ":" + "3-3"
                            from_dest.send(payload.encode('utf-8'))
                            print("NATBox: Client not found")

                elif ip_from[:3] == "212" and ip_to[:3] != "146":
                    dest = clients[ip_from]

                    payload = self.nat_ip + ":Pacquet dropped unable to send to an external client"
                    dest.send(payload.encode('utf-8'))

                    print("NATBox: Pacquet dropped (Ext -> Ext)")

    # Start a timer for a nat table entry
    def start_timer(self, ip_from, t):
        NAT_Timer[ip_from] = t

        ip_to = NAT_Table[ip_from]
        print("NAT Table entry created between %s and %s for 30 seconds" % (ip_from, ip_to))

        while NAT_Timer[ip_from]:
            time.sleep(1)
            NAT_Timer[ip_from] -= 1

        print("NAT Table entry expired for %s and %s" % (ip_from, ip_to))

        NAT_Timer[ip_from] = 0
        NAT_Table[ip_from] = ""

    def closeConnection(self):
        self.nat_UDPSocket.close()
        self.nat_TCPSocket.close()

    def get_host_info(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        MAC_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP, MAC_address


def print_line():
    print("##########################################################################################################")


def make_pool(limit):
    count = 0
    third = 0
    port = 80

    for i in range(limit):
        if count > 255:
            count = 0
            third += 1
            ip = "192.168." + str(third) + "." + str(count) + ":" + str(port)
            int_ips.append(ip)
            pool.append(ip)

        ip = "192.168." + str(third) + "." + str(count) + ":" + str(port)
        int_ips.append(ip)
        pool.append(ip)
        count += 1
        port += 1


def init_table():
    for internal_ip in pool:
        NAT_Table[internal_ip] = ""
        NAT_Timer[internal_ip] = 0.0


if __name__ == '__main__':
    make_pool(5)
    init_table()

    thread = threading.Thread(target=initializeNAT, args=())
    thread.start()
