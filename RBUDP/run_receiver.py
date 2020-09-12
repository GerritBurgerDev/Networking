import socket
import os
import receiver
import sys

gw = os.popen("ip -4 route show default").read().split()
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((gw[2], 0))
receiver_ip = s.getsockname()[0]  # Receiver IP
udp_port = 5001  # UDP port


# run Receiver
def runReceiver(receiver_ip, sender_ip, tcp_port, udp_port):
    receiver.run(receiver_ip, sender_ip, tcp_port, udp_port)


if __name__ == "__main__":
    sender_ip = sys.argv[1]  # sender ip
    tcp_port = int(sys.argv[2])  # sender tcp port
    runReceiver(str(receiver_ip), str(sender_ip), tcp_port, udp_port)
