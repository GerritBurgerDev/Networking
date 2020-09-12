from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *
from socket import *
import pyaudio
import struct
import time
import os
import mute_alsa
import pickle
import _thread

addresses = {}
groups = {}
address_nick = {}
clients = {}
clients_ports = {}
get_address = {}
get_sockets = {}
users = {}
group_channels = {}
group_members = {}
vn_sockets = {}

ports = []
group_ips = []
PORT = 8000
BUFSIZ = 1024

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


class Communicator(QtCore.QObject):
    message = QtCore.Signal(object)


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class Ui_Frame(QtWidgets.QWidget):
    global CHOICE

    def setup_Ui(self, Frame):
        self.p = pyaudio.PyAudio()
        self.running = True
        self.multicasting = False
        self.connected = False

        self.Frame = Frame
        self.Frame.setObjectName(_fromUtf8("Frame"))
        self.Frame.resize(692, 540)
        self.Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Frame.setStyleSheet("background-color: #3b3b3b")
        self.Frame.setFixedSize(QSize(700, 510))

        self.quit_button = QtWidgets.QPushButton(self.Frame)
        self.quit_button.setGeometry(QtCore.QRect(560, 460, 90, 27))
        self.quit_button.setObjectName(_fromUtf8("quitButton"))
        self.quit_button.clicked.connect(self.close_window)
        self.quit_button.setStyleSheet(
            "QPushButton { background-color: #b32020; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; } \
             QPushButton:hover { background-color: #942222; } ")

        self.Users = QtWidgets.QFrame(self.Frame)
        self.Users.setGeometry(QtCore.QRect(430, 10, 251, 190))
        self.Users.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Users.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Users.setObjectName(_fromUtf8("Users"))
        self.Users.setStyleSheet("background-color: #cccccc")

        self.User_list = QtWidgets.QLabel(self.Users)
        self.User_list.setGeometry(QtCore.QRect(50, 10, 141, 21))

        self.Groups = QtWidgets.QFrame(self.Frame)
        self.Groups.setGeometry(QtCore.QRect(430, 210, 251, 190))
        self.Groups.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Groups.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Groups.setObjectName(_fromUtf8("Groups"))
        self.Groups.setStyleSheet("background-color: #cccccc")

        self.room_Label = QtWidgets.QLabel(self.Groups)
        self.room_Label.setGeometry(QtCore.QRect(50, 10, 141, 21))

        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Latin Modern Sans Quotation"))
        font.setPointSize(20)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)

        self.User_list.setFont(font)
        self.User_list.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.User_list.setIndent(16)
        self.User_list.setObjectName(_fromUtf8("Userlist"))

        self.scrollable = QtWidgets.QScrollArea(self.Users)
        self.scrollable.setGeometry(0, 40, 251, 190)
        self.list_widget = QtWidgets.QListWidget(self.scrollable)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget.resize(251, 190)

        self.room_Label.setFont(font)
        self.room_Label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.room_Label.setIndent(16)
        self.room_Label.setObjectName(_fromUtf8("roomLabel"))

        self.scrollable_rooms = QtWidgets.QScrollArea(self.Groups)
        self.scrollable_rooms.setGeometry(0, 40, 251, 190)
        self.list_widget_rooms = QtWidgets.QListWidget(self.scrollable_rooms)
        self.list_widget_rooms.resize(251, 190)

        self.show_messages = QtWidgets.QTextEdit(self.Frame)
        self.show_messages.setGeometry(QtCore.QRect(10, 10, 401, 391))
        self.show_messages.setObjectName(_fromUtf8("show_messages"))
        self.show_messages.setStyleSheet("background-color: #cccccc; \
                                         border-left: 4px solid #b32020; \
                                         padding-left: 4px;")
        self.show_messages.setReadOnly(True)

        self.type_message = QtWidgets.QTextEdit(self.Frame)
        self.type_message.setGeometry(QtCore.QRect(10, 420, 401, 71))
        self.type_message.setObjectName(_fromUtf8("type_message"))
        self.type_message.setDisabled(True)
        self.type_message.setStyleSheet("border: none; \
                                        border-bottom: 2px solid #b32020; \
                                        background-color: #cccccc;")

        self.show_messages.raise_()
        self.type_message.raise_()
        self.Users.raise_()
        self.quit_button.raise_()

        self.retranslate_Ui(self.Frame)
        self.comm = Communicator()
        self.rooms = Communicator()
        self.comm.message.connect(self.receive)
        self.rooms.message.connect(self.update_rooms)

        QtCore.QMetaObject.connectSlotsByName(self.Frame)

    def retranslate_Ui(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.quit_button.setText(_translate("Frame", "Quit", None))
        self.User_list.setText(_translate("Frame", "Users", None))
        self.room_Label.setText(_translate("Frame", "Rooms", None))

    def close_window(self):
        global app
        import sys
        self.running = False

        for s in addresses:
            send = ["server_quit", "lOlOzIeZ"]
            s.send(pickle.dumps(send).ljust(1024))

        try:
            app.closeAllWindows()
        except:
            sys.exit()

    def update_rooms(self, array):
        self.list_widget_rooms.clear()

        rooms = array[0]
        for room in rooms:
            item = QtWidgets.QListWidgetItem(self.list_widget_rooms)
            item.setText(room)

    def online_users(self, users):
        self.list_widget.clear()

        for user in users:
            item = QtWidgets.QListWidgetItem(self.list_widget)
            item.setText(user)

    def receive(self, msg):
        if msg[0] == "@":
            red_Text = "<span style=\" color:#8080ff;\" >"
            red_Text = red_Text + msg + "</span>"
            self.show_messages.append(red_Text)

        elif msg[0] == "~":
            blue_text = "<span style=\" color:#ff0000;\" >"
            blue_text = blue_text + msg[1:] + "</span>"
            self.show_messages.append(blue_text)

        elif msg[0] == "`":
            green_text = "<span style=\" color:black;\" >"
            green_text = green_text + msg[1:] + "</span>"
            self.show_messages.append(green_text)


        else:
            self.show_messages.append(msg)


BUFSIZ = 1024


class client:
    def __init__(self, tcp_socket, tcp_port, udp_port, ip):
        global users
        global ui

        self.tcp_port = tcp_port
        self.tcp_socket = tcp_socket
        self.udp_port = udp_port
        self.ip = self.get_ip()
        self.address = addresses[self.tcp_socket]

        name = self.tcp_socket.recv(BUFSIZ)
        rec_array = pickle.loads(name)

        name = rec_array[0]

        while name in users:
            array = ["Nickname already in use, please try again!"]
            array = pickle.dumps(array)
            array = array.ljust(1024)
            self.tcp_socket.send(array)
            r_array = pickle.loads(self.tcp_socket.recv(BUFSIZ))
            name = r_array[0]

        array = [1]
        ui.comm.message.emit("~" + name + " " + "has joined the server")
        array = pickle.dumps(array)
        array = array.ljust(1024)
        self.tcp_socket.send(array)

        address_nick[ip] = name
        self.nickname = name
        get_address[name] = ip
        users[name] = addresses[self.tcp_socket]
        clients[self.tcp_socket] = name
        get_sockets[ip] = self.tcp_socket

        send = ["port", self.udp_port]
        self.tcp_socket.send(pickle.dumps(send).ljust(1024))

        self.broadcast(users)
        self.handler()

    def get_ip(self):
        gw = os.popen("ip -4 route show default").read().split()
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect((gw[2], 0))
        receiver_ip = s.getsockname()[0]
        return receiver_ip

    # call = make call [0,from,to] then reply = 0 is accept, 1 is reject
    # receive_call = receive call [1,from] accept reply with 0 reject reply with 1
    # create channel = ["create_channel", "channel_name"]
    # join_channel = ["join_channel", "channel_name"]
    # leave_channel = ["leave_channel", "channel_name"]
    # delete_channel = ["delete_channel", "channel_name"]

    def broadcast(self, array):
        """Broadcasts a message to all the clients."""
        array = pickle.dumps(array).ljust(1024)

        for sock in clients:
            sock.send(array)

    def handler(self):
        global ui

        while ui.running:
            r = self.tcp_socket.recv(1024)

            if r == b'':
                pass
            else:
                r = pickle.loads(r)

                if r[0] == "connecting":
                    client = get_sockets[r[1]]

                    names = []
                    for name in group_channels:
                        names.append(name)

                    get_users = []
                    for user in users:
                        get_users.append(user)

                    ui.online_users(get_users)

                    ip = "224.0.0.0"

                    send = ["connecting", names, ip]
                    client.send(pickle.dumps(send).ljust(1024))

                if r[0] == "reject":
                    client = get_sockets[r[2]]
                    ui.comm.message.emit("~" + name + " is calling " + r[2])
                    if len(r) == 4:
                        msg = ["reject", r[1], r[3]]
                    else:
                        msg = ["reject", r[1]]
                    msg = pickle.dumps(msg).ljust(1024)
                    client.send(msg)

                if r[0] == "group_call":
                    group_users = r[1]
                    mc_ip = group_ips.pop(1)
                    groups[mc_ip] = r[1]

                    get_ips = []
                    for name in group_users:
                        get_ips.append(get_address[name])

                    for ip in get_ips:
                        receiver = get_sockets[ip]
                        send = ["group_call", get_ips, mc_ip]
                        receiver.send(pickle.dumps(send).ljust(1024))

                if r[0] == "call":
                    name = address_nick[r[1]]
                    ui.comm.message.emit("~" + name + " is calling " + r[2])
                    for client in clients:
                        if clients[client] == r[2]:
                            # Get the client you want to send to
                            receiver = client

                            # Send a receive call to the receiver
                            send = ["receive_call", address_nick[r[1]], r[1], clients_ports[r[1]]]
                            receiver.send(pickle.dumps(send).ljust(1024))

                if r[0] == "receive_call":
                    if r[1] == 1:
                        name = address_nick[r[2]]
                        ui.comm.message.emit("~" + name + " accepted call from " + r[3])
                        for client in clients:
                            if clients[client] == r[3]:
                                # Get the client you want to send to
                                receiver = client

                                # Send a receive call to the receiver
                                send = ["call_accepted", r[2], clients_ports[r[2]]]
                                receiver.send(pickle.dumps(send).ljust(1024))
                    else:
                        ui.comm.message.emit("~" + address_nick[r[2]] + " rejected call from " + r[3])
                        for client in clients:
                            if clients[client] == r[3]:
                                # Get the client you want to send to
                                receiver = client

                                # Send a receive call to the receiver
                                send = ["call_rejected", r[2], clients_ports[r[2]]]
                                receiver.send(pickle.dumps(send).ljust(1024))

                if r[0] == "{quit}":
                    name = address_nick[r[1]]
                    ui.comm.message.emit("~" + name + " has quit the server")
                    get_client = get_sockets[r[1]]

                    name = clients[get_client]
                    ip = get_address[name]

                    for channel_name in group_members:
                        if ip in group_members[channel_name]:
                            group_members[channel_name].remove(ip)

                    del clients[get_client]
                    del users[name]

                    names = []
                    for name in users:
                        names.append(name)

                    get_users = []
                    for user in users:
                        get_users.append(user)

                    ui.online_users(get_users)

                    if len(users) != 0:
                        self.broadcast(users)

                if r[0] == "create_channel":
                    created_by = address_nick[r[2]]
                    ui.comm.message.emit("~Channel " + r[1] + " created by " + created_by)
                    if r[1] in group_channels:
                        send = ["create_channel", "name_taken"]
                        self.tcp_socket.send(pickle.dumps(send).ljust(1024))
                    else:
                        ip = group_ips.pop(1)
                        group_channels[r[1]] = ip
                        group_members[r[1]] = []

                        names = []
                        for name in group_channels:
                            names.append(name)

                        array = [names]
                        ui.rooms.message.emit(array)

                        broadcast_this = [names, ip]
                        self.broadcast(broadcast_this)

                        send = ["create_channel", "great_success", names, ip]
                        self.tcp_socket.send(pickle.dumps(send).ljust(1024))

                if r[0] == "join_channel":
                    joining = address_nick[r[2]]
                    mc_ip = group_channels[r[1]]
                    group_members[r[1]].append(self.address)
                    ui.comm.message.emit("~" + joining + " has joined channel " + r[1])

                    members = []
                    for name in group_members:
                        members.append(name)

                    for a in addresses:
                        if addresses[a] in group_members[r[1]]:
                            send = ["join_channel", group_members[r[1]], r[1], members, mc_ip]
                            a.send(pickle.dumps(send).ljust(1024))

                if r[0] == "leave_channel":
                    leaving = address_nick[r[2]]
                    ui.comm.message.emit("~" + leaving + " has leaved channel " + r[1])
                    for a in addresses:
                        if addresses[a] in group_members[r[1]] and a != self.address:
                            send = ["leave_channel", self.address]
                            a.send(pickle.dumps(send).ljust(1024))

                        if a == self.address:
                            send = ["leave_channel_self", self.address]
                            a.send(pickle.dumps(send).ljust(1024))

                    group_members[r[1]].remove(r[2])

                if r[0] == "delete_channel":
                    deleting = address_nick[r[2]]
                    ui.comm.message.emit("~" + deleting + " has deleted channel " + r[1])
                    del group_channels[r[1]]

                    names = []
                    for name in group_channels:
                        names.append(name)

                    broadcast_this = [names, "224.0.0.0"]
                    self.broadcast(broadcast_this)

                    array = [names]
                    ui.rooms.message.emit(array)

                    send = ["delete_channel", names, r[1]]
                    send = pickle.dumps(send).ljust(1024)

                    socket = get_sockets[r[2]]
                    socket.send(send)

                    for name in group_members:
                        for ip in group_members[name]:
                            socket = get_sockets[ip]
                            socket.send(send)

                    del group_members[r[1]]

                if r[0] == "message":
                    for user in r[2]:
                        ui.comm.message.emit("@" + r[1] + " to @" + user + ": " + r[3])
                    fr = r[1]

                    for user in r[2]:
                        send = ["message", fr, user, r[3]]
                        for sock in clients:
                            if clients[sock] == user:
                                sock.send(pickle.dumps(send).ljust(1024))
                                break

                if r[0] == "call_disconnect":
                    receiver = get_sockets[r[1]]
                    name = address_nick[r[1]]
                    ui.comm.message.emit("~" + "call between " + name + " and " + r[2] + " has been disconnected")
                    send = ["call_disconnect", "lol"]
                    send = pickle.dumps(send).ljust(1024)
                    receiver.send(send)

                if r[0] == "group_disconnect":
                    for u in groups[r[1]]:
                        s = get_sockets[users[u]]
                        send = ["group_disconnect", "loliez"]
                        s.send(pickle.dumps(send).ljust(1024))


def get_ip():
    gw = os.popen("ip -4 route show default").read().split()
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect((gw[2], 0))
    receiver_ip = s.getsockname()[0]
    return receiver_ip


def connect(tcp_port):
    global app
    global Frame
    global ui

    server_ip = get_ip()
    tcp_sock = socket(AF_INET, SOCK_STREAM)
    tcp_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_sock.bind((server_ip, tcp_port))
    tcp_sock.listen(1)

    while True:
        TCP_socket, addr = tcp_sock.accept()
        addresses[TCP_socket] = addr[0]
        port = ports.pop(-1)
        clients_ports[addr[0]] = port

        _thread.start_new_thread(client, (TCP_socket, tcp_port, port, addr[0],))
        _thread.start_new_thread(vn, (server_ip, port,))


def vn(server_ip, tcp_port):
    global ui

    original_tcp_port = tcp_port
    tcp_port = tcp_port + 100
    tcp_sock_recv = socket(AF_INET, SOCK_STREAM)
    tcp_sock_recv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_sock_recv.bind((server_ip, tcp_port))
    tcp_sock_recv.listen(1)
    TCP_socket_recv, addr = tcp_sock_recv.accept()

    tcp_port = tcp_port + 100
    tcp_sock_send = socket(AF_INET, SOCK_STREAM)
    tcp_sock_send.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_sock_send.bind((server_ip, tcp_port))
    tcp_sock_send.listen(1)

    TCP_socket_send, addr = tcp_sock_send.accept()

    vn_sockets[original_tcp_port] = TCP_socket_send

    sender_ip = [ip for ip in clients_ports if clients_ports[ip] == original_tcp_port]

    sender_name = address_nick[sender_ip[0]]

    while ui.running:
        rec_users = TCP_socket_recv.recv(1024)
        if rec_users == b'':
            continue

        rec_users = pickle.loads(rec_users)
        send_ports = []

        for u in rec_users:
            ui.comm.message.emit("~" + sender_name + " sent a voicenote to " + u)
            send_ports.append(clients_ports[users[u]])

        data = TCP_socket_recv.recv(1024)
        frames = []

        while data != b'vN_dOnE':
            frames.append(data)
            data = TCP_socket_recv.recv(1024)

        send = [sender_name]
        for p in send_ports:
            sock = vn_sockets[p]
            sock.send(pickle.dumps(send).ljust(1024))
            for c in frames:
                sock.send(c)
            sock.send(b'vN_dOnE')
            time.sleep(0.0001)


def create_ports():
    for i in range(5000, 10001):
        ports.append(i)


def create_group_ips():
    start = "224.0.0."

    for i in range(1, 255):
        ip = start + str(i)
        group_ips.append(ip)


if __name__ == '__main__':
    global Frame
    global app
    global ui

    import sys

    app = QtWidgets.QApplication(sys.argv)
    Frame = QtWidgets.QFrame()

    ui = Ui_Frame()
    ui.setup_Ui(Frame)
    Frame.show()

    _thread.start_new_thread(create_group_ips, ())
    _thread.start_new_thread(create_ports, ())
    _thread.start_new_thread(connect, (5000,))
    sys.exit(app.exec_())
