from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *
import socket
import time
import sys
import os
import math
import pickle
import _thread

ui = None
app = None

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


class Communicator(QtCore.QObject):
    message = Signal(object)


class Ui_Frame(QtWidgets.QWidget):
    def setupUi(self, Frame):
        Frame.setObjectName(_fromUtf8("Frame"))
        Frame.resize(583, 357)
        Frame.setMaximumSize(QtCore.QSize(583, 357))
        Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        Frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.filename = None
        self.pressedUDP = False
        self.pressedTCP = False

        self.textEdit = QtWidgets.QTextEdit(Frame)
        self.textEdit.setGeometry(QtCore.QRect(10, 10, 361, 301))
        self.textEdit.setObjectName(_fromUtf8("textEdit"))

        self.pushButton = QtWidgets.QPushButton(Frame)
        self.pushButton.setGeometry(QtCore.QRect(430, 10, 100, 41))
        self.pushButton.setMaximumSize(QtCore.QSize(110, 41))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.pushButton.clicked.connect(self.sendTCP)

        self.pushButton_2 = QtWidgets.QPushButton(Frame)
        self.pushButton_2.setGeometry(QtCore.QRect(430, 60, 100, 41))
        self.pushButton_2.setMaximumSize(QtCore.QSize(110, 41))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.pushButton_2.clicked.connect(self.sendUDP)

        self.timeTaken = QtWidgets.QLabel(Frame)
        self.timeTaken.setGeometry(QtCore.QRect(440, 120, 100, 15))
        self.timeTaken.setObjectName(_fromUtf8("timeTaken"))
        self.timeTakenResult = QtWidgets.QLabel(Frame)
        self.timeTakenResult.setGeometry(QtCore.QRect(440, 145, 100, 15))
        self.timeTakenResult.setObjectName(_fromUtf8("timeTakenResult"))

        self.throughput = QtWidgets.QLabel(Frame)
        self.throughput.setGeometry(QtCore.QRect(440, 170, 155, 20))
        self.throughput.setObjectName(_fromUtf8("throughput"))
        self.throughput_result = QtWidgets.QLabel(Frame)
        self.throughput_result.setGeometry(QtCore.QRect(440, 195, 100, 20))
        self.throughput_result.setObjectName(_fromUtf8("throughputResult"))

        self.pushButton_3 = QtWidgets.QPushButton(Frame)
        self.pushButton_3.setGeometry(QtCore.QRect(380, 310, 90, 41))
        self.pushButton_3.setMaximumSize(QtCore.QSize(90, 41))
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.pushButton_3.clicked.connect(self.getFile)

        self.pushButton_4 = QtWidgets.QPushButton(Frame)
        self.pushButton_4.setGeometry(QtCore.QRect(480, 310, 90, 41))
        self.pushButton_4.setMaximumSize(QtCore.QSize(90, 41))
        self.pushButton_4.setObjectName(_fromUtf8("pushButton_4"))
        self.pushButton_4.clicked.connect(self.quit)

        self.retranslateUi(Frame)
        self.comm = Communicator()
        self.text = Communicator()
        self.time = Communicator()
        self.tr = Communicator()
        self.text.message.connect(self.setMessage)
        self.time.message.connect(self.setTimeTaken)
        self.tr.message.connect(self.setThroughput)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def quit(self):
        app.closeAllWindows()

    def setTimeTaken(self, time):
        self.timeTakenResult.setText(time)

    def sendUDP(self):
        self.pressedUDP = True

    def sendTCP(self):
        self.pressedTCP = True

    def getFile(self):
        name, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File')
        self.getFileName(name)

    def getFileName(self, name):
        self.filename = name.split("/")[-1]
        self.ext = name.split(".")[-1]

        self.textEdit.append("The file %s has been selected." % self.filename)

    def setMessage(self, msg):
        self.textEdit.append(msg)

    def setThroughput(self, msg):
        self.throughput_result.setText(msg)

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.pushButton.setText(_translate("Frame", "Send via TCP", None))
        self.pushButton_2.setText(_translate("Frame", "Send via UDP", None))
        self.pushButton_3.setText(_translate("Frame", "Select file", None))
        self.pushButton_4.setText(_translate("Frame", "Quit", None))
        self.timeTaken.setText(_translate("Frame", "Time taken:", None))
        self.throughput.setText(_translate("Frame", "Throughput:", None))


# Initializes sender TCP and UDP sockets
class initializeSender:
    def __init__(self, server_TCPPort):
        self.server_TCPPort = server_TCPPort
        self.current_server_UDPPort = 5000
        self.initializeConnection()

    def initializeConnection(self):
        # wait for TCP connection from client
        self.server_TCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket
        self.server_name = self.get_ip()
        print("Sender IP", self.server_name)
        self.server_TCPSocket.bind((self.server_name, self.server_TCPPort))
        self.server_TCPSocket.listen(1)

        print('Server: Listening for connections')

        connection_TCPSocket, addr = self.server_TCPSocket.accept()
        senderSession(self.server_name, self.current_server_UDPPort, connection_TCPSocket)  # Creates sender session

    def closeConnection(self):
        self.server_TCPSocket.close()

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


# Creates sender session and sends data
class senderSession:
    def __init__(self, serverName, server_UDPPort, connection_TCPSocket):
        self.server_name = serverName
        self.server_UDPPort = server_UDPPort
        # self.buffer_size = 2048
        self.connection_TCPSocket = connection_TCPSocket
        self.sendData()
        # try:
        #     self.sendData()
        # except:
        #     print("Receiver disconnected")
        #     ui.text.message.emit("Receiver disconnected")

    def closeConnection(self):
        print('Closing thread connection')
        self.server_UDPSocket.close()
        self.connection_TCPSocket.close()

    def sendData(self):
        global ui

        # start a UDP session to send packets over
        client_addr = self.connection_TCPSocket.recv(1024)
        self.client_name, self.client_UDPPort = pickle.loads(client_addr)
        self.server_UDPSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
        self.server_UDPSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_UDPSocket.bind((self.server_name, self.server_UDPPort))
        self.data_dict = {}
        self.clist = []
        self.buffer_size = 1024

        print("Server: Awaiting filename from client")
        while True:
            while True:
                self.filename = None

                # Wait till one of protocols are chosen
                while True:
                    if (ui.pressedUDP == True or ui.pressedTCP == True):
                        self.filename = ui.filename
                        break

                print("SENDING FILE DATA.... ")

                file_size = os.path.getsize(ui.filename)
                self.filesize = file_size
                send = []
                send.append(self.filename)
                send.append(file_size)
                send = pickle.dumps(send).ljust(1024)
                self.connection_TCPSocket.send(send)

                # TCP File transfer
                if (ui.pressedTCP == True):
                    ui.pressedTCP = False

                    send = []
                    send.append("TCP")
                    send = pickle.dumps(send).ljust(1024)
                    self.connection_TCPSocket.send(send)
                    start = time.time()
                    file = open(ui.filename, 'rb')
                    data = file.read(self.buffer_size)
                    t = 0
                    # Send file data
                    while (data):
                        self.connection_TCPSocket.send(data)
                        data = file.read(self.buffer_size)

                    end = time.time()
                    print(self.filesize/1000000)
                    tp = round((self.filesize / 1000000) / (end - start), 4)
                    elapsed = round(end - start, 4)
                    ui.time.message.emit(str(elapsed) + "s")
                    ui.text.message.emit("File has been successfully sent.")
                    ui.tr.message.emit(str(tp) + "mb/s")
                    file.close()
                    break
                else:
                    # TCP signal
                    send = []
                    send.append("UDP")
                    send = pickle.dumps(send).ljust(1024)
                    self.connection_TCPSocket.send(send)

                if os.path.isfile(self.filename):
                    file_size = os.path.getsize(self.filename)

                    blocks = math.ceil(file_size / self.buffer_size)
                    self.connection_TCPSocket.send(str(blocks).encode('utf-8'))
                    self.blocks = blocks

                    break

                else:
                    self.connection_TCPSocket.send('0'.encode('utf-8'))
                    print("Server: File does not exist. Continue waiting for filename")

            # RBUDP File transfer
            if (ui.pressedUDP == True):
                ui.pressedUDP = False
                with open(self.filename, 'rb') as f:
                    self.data_dict.clear()
                    print("Server: Sending data over...")
                    data = f.read(self.buffer_size)
                    segment_id = 0
                    time.sleep(0.1)
                    timeSending = 0
                    count = 0
                    bool = True
                    send = 0

                    if file_size <= 1000000:
                        bool = False

                    s = time.time()
                    while (data):
                        self.clist.append(segment_id)
                        segment_id_bytes = segment_id.to_bytes(4, byteorder='big')
                        data = segment_id_bytes + data
                        self.data_dict[segment_id] = data

                        if count <= int(0.5*self.blocks):
                            send += 1
                            self.server_UDPSocket.sendto(data, (self.client_name, self.client_UDPPort))

                        data = f.read(self.buffer_size)
                        segment_id += 1
                        progress = ((segment_id / blocks) * 100)
                        count += 1

                    end = time.time()
                    timeSending = end - s

                    print(send)
                    # TCP signal
                    send = []
                    send.append("Done")
                    send = pickle.dumps(send).ljust(1024)
                    self.connection_TCPSocket.sendall(send)

                    while True:
                        missing_bytes = self.connection_TCPSocket.recv(1024)

                        try:
                            mes = missing_bytes.decode('utf-8')
                            if mes == "CHUNCK":
                                ui.text.message.emit("File has been successfully sent.")
                                e = time.time()
                                elap = round(e - s, 4)
                                ui.time.message.emit(str(elap) + "s")
                                tp = round(((count * self.buffer_size) / 1000000) / timeSending, 4)
                                ui.tr.message.emit(str(tp) + "mb/s")
                                break
                        except:
                            pass

                        # Missing packet ids
                        missing = [int.from_bytes(missing_bytes[i:i + 4], byteorder='big') for i in
                                   range(0, len(missing_bytes), 4)]


                        t2 = time.time()
                        for idx in missing:
                            count += 1
                            if idx <= self.blocks:
                                self.server_UDPSocket.sendto(self.data_dict[idx], (self.client_name, self.client_UDPPort))
                            else:
                                print(idx)
                        t3 = time.time()
                        timeSending += (t3 - t2)

                        # TCP signal
                        send = []
                        send.append("Done")
                        send = pickle.dumps(send).ljust(1024)
                        self.connection_TCPSocket.sendall(send)


def runGUI():
    global ui
    global app

    app = QtWidgets.QApplication(sys.argv)
    frame = QtWidgets.QFrame()

    ui = Ui_Frame()
    ui.setupUi(frame)
    frame.show()

    sys.exit(app.exec_())


def run(server_TCPPort):
    global ui
    global app

    app = QtWidgets.QApplication(sys.argv)
    frame = QtWidgets.QFrame()

    ui = Ui_Frame()
    ui.setupUi(frame)
    frame.show()

    _thread.start_new_thread(initializeSender, (server_TCPPort,))
    sys.exit(app.exec_())
