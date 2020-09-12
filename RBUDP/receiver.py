from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *
import select
import socket
import time
import sys
import os
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
    message = QtCore.Signal(object)


# GUI class
class Ui_Frame(QtWidgets.QWidget):
    def setupUi(self, Frame):
        Frame.setObjectName(_fromUtf8("Frame"))
        Frame.resize(583, 357)
        Frame.setMaximumSize(QtCore.QSize(500, 357))
        Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        Frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.filename = None
        self.pressed_udp = False
        self.pressed_tcp = False

        self.progress_bar = QtWidgets.QProgressBar(Frame)
        self.progress_bar.setGeometry(QtCore.QRect(10, 320, 361, 21))
        self.progress_bar.setMaximumSize(QtCore.QSize(361, 21))
        self.progress_bar.setProperty("value", 0)
        self.progress_bar.setObjectName(_fromUtf8("progressBar"))

        self.text_edit = QtWidgets.QTextEdit(Frame)
        self.text_edit.setGeometry(QtCore.QRect(10, 10, 361, 301))
        self.text_edit.setObjectName(_fromUtf8("textEdit"))

        self.time_taken = QtWidgets.QLabel(Frame)
        self.time_taken.setGeometry(QtCore.QRect(390, 20, 100, 15))
        self.time_taken.setObjectName(_fromUtf8("timeTaken"))
        self.time_taken_result = QtWidgets.QLabel(Frame)
        self.time_taken_result.setGeometry(QtCore.QRect(390, 45, 100, 15))
        self.time_taken_result.setObjectName(_fromUtf8("timeTakenResult"))

        self.packetloss = QtWidgets.QLabel(Frame)
        self.packetloss.setGeometry(QtCore.QRect(390, 70, 100, 15))
        self.packetloss.setObjectName(_fromUtf8("packetLoss"))
        self.packetloss_percentage = QtWidgets.QLabel(Frame)
        self.packetloss_percentage.setGeometry(QtCore.QRect(390, 95, 100, 15))
        self.packetloss_percentage.setObjectName(_fromUtf8("packetLossPercentage"))

        self.push_button_4 = QtWidgets.QPushButton(Frame)
        self.push_button_4.setGeometry(QtCore.QRect(390, 310, 90, 41))
        self.push_button_4.setMaximumSize(QtCore.QSize(90, 41))
        self.push_button_4.setObjectName(_fromUtf8("pushButton_4"))
        self.push_button_4.clicked.connect(self.quit)

        self.retranslateUi(Frame)
        self.prog = Communicator()
        self.text = Communicator()
        self.packetloss = Communicator()
        self.time = Communicator()
        self.text.message.connect(self.setMessage)
        self.prog.message.connect(self.setProgress)
        self.packetloss.message.connect(self.setPacketLoss)
        self.time.message.connect(self.setTimeTaken)
        QtCore.QMetaObject.connectSlotsByName(Frame)

    def quit(self):
        app.closeAllWindows()

    def sendUDP(self):
        self.pressed_udp = True

    def sendTCP(self):
        self.pressed_tcp = True

    def setMessage(self, msg):
        self.text_edit.append(msg)

    def getFile(self):
        name, filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File')
        self.getFileName(name)

    def setTimeTaken(self, time):
        self.time_taken_result.setText(time)

    def setPacketLoss(self, val):
        self.packetloss_percentage.setText(val)

    def getFileName(self, name):
        self.filename = name.split("/")[-1]
        self.ext = name.split(".")[-1]

        self.text_edit.append("The file %s has been selected." % self.filename)

    def setProgress(self, val):
        self.progress_bar.setProperty("value", val)

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.push_button_4.setText(_translate("Frame", "Quit", None))
        self.time_taken.setText(_translate("Frame", "Time taken:", None))
        self.time_taken_result.setText(_translate("Frame", "0.00s", None))
        self.packetloss.setText(_translate("Frame", "Packetloss:", None))
        self.packetloss_percentage.setText(_translate("Frame", "0.00%:", None))


# Creates client session
class ClientSession:
    def __init__(self, clientName, client_UDPPort, serverName, server_TCPPort):
        # initialize variables
        self.client_name = clientName
        self.client_udpport = int(client_UDPPort)
        self.server_name = serverName
        self.server_tcpport = server_TCPPort
        self.filename = None
        self.segmentid_list = []
        self.bytesarray = b''
        self.bytes_d = {}
        self.initializeConnection()

    def closeConnection(self):
        self.client_tcpsocket.close()
        self.client_udpsocket.close()

    def initializeConnection(self):
        # create UDP socket
        self.client_udpsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_udpsocket.bind((self.client_name, self.client_udpport))

        # create TCP socket
        self.client_tcpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # setup 3-way handshake
        self.client_tcpsocket.connect((self.server_name, self.server_tcpport))

        # send over information about UDP socket
        self.client_tcpsocket.send(pickle.dumps((self.client_name, self.client_udpport)))
        print("Client: Successfully connected to server")

        self.receiveData()

    def receiveData(self):
        global ui

        msg = "Connected to the sender"
        ui.text.message.emit(msg)

        while True:
            # give user option to choose file if filename not specified
            try:
                self.bytes_d.clear()
                self.segmentid_list.clear()
                data = pickle.loads(self.client_tcpsocket.recv(1024))

                self.filename = data[0]
                self.filesize = data[1]
                msg = "The file " + (self.filename) + ", is being received."
                ui.text.message.emit(msg)

                protocol = pickle.loads(self.client_tcpsocket.recv(1024))
                protocol = protocol[0]
                print("Client: Receiving data...")

                packetloss = 0
                transmission_count = 0
                time.sleep(0.01)

                count = 0

                # RBUDP protocol selected
                if protocol == "UDP":
                    ui.prog.message.emit(0)

                    msg = "UDP File transfer being used."
                    ui.text.message.emit(msg)

                    msg = "Waiting for data..."
                    ui.text.message.emit(msg)

                    self.blocks = int(self.client_tcpsocket.recv(1024).decode('utf-8'))

                    start_time = time.time()
                    while True:
                        while True:
                            ready = select.select([self.client_udpsocket], [], [], 0.00001)

                            while ready[0]:
                                data = self.client_udpsocket.recv(1026)
                                self.segmentid_list.append(int.from_bytes(data[0:2], byteorder='big'))

                                count += 1

                                progress = (count / self.blocks) * 100
                                ui.prog.message.emit(progress)

                                self.bytes_d[int.from_bytes(data[0:2], byteorder='big')] = data[2:]
                                ready = select.select([self.client_udpsocket], [], [], 0.00001)

                            ready2 = select.select([self.client_tcpsocket], [], [], 0.00001)

                            if ready2[0]:
                                string = pickle.loads(self.client_tcpsocket.recv(1024))
                                transmission_count += 1
                                break

                        missing = self.missing_elements(sorted(self.segmentid_list), 0, self.blocks - 1)
                        packetloss += len(missing)

                        if len(missing) == 0:
                            print("Client: File is fully received. Yay!")

                            self.client_tcpsocket.send("CHUNCK".encode('utf-8'))

                            break
                        else:
                            missingbytes = b''

                            for idx in missing:
                                missingbytes += idx.to_bytes(2, byteorder='big')

                            self.client_tcpsocket.send(missingbytes)

                    end_time = time.time()

                    self.assembleData()

                    time_taken = round(end_time - start_time, 4)
                    ui.time.message.emit(str(time_taken) + "s")
                    packetloss_percentage = round((packetloss / (self.blocks )), 2) * 100
                    ui.packetloss.message.emit(str(packetloss_percentage) + "%")

                # TCP protocol selected
                else:
                    ui.packetloss.message.emit("0.00" + "s")
                    ui.prog.message.emit(0)

                    msg = "TCP File transfer being used."
                    ui.text.message.emit(msg)

                    start_time = time.time()

                    amount_recv = 0
                    data = self.client_tcpsocket.recv(1024)
                    amount_recv += 1024

                    f = open(self.filename, 'wb')
                    f.write(data)

                    # Recieve all data
                    while amount_recv < self.filesize:
                        progress = (amount_recv / self.filesize) * 100
                        ui.prog.message.emit(progress)

                        data = self.client_tcpsocket.recv(1024)
                        size = data.__sizeof__()
                        amount_recv += (size - 33)

                        f.write(data)

                    end_time = time.time()

                    time_taken = round(end_time - start_time, 4)
                    ui.time.message.emit(str(time_taken) + "s")
                    ui.prog.message.emit(100)

                    f.close()

                    msg = "TCP file transfer complete."
                    ui.text.message.emit(msg)
                    print("Client: TCP file transfer complete.")
            except:
                pass

    def assembleData(self):
        global ui

        split_filename = os.path.splitext(self.filename)
        new_filename = split_filename[0] + split_filename[1]
        with open(new_filename, 'wb') as f:
            for i in range(self.blocks):
                d = self.bytes_d[i]
                f.write(d)

        print("Client: File is successfully downloaded!")
        msg = "UDP file transfer complete"
        ui.text.message.emit(msg)

    def missing_elements(self, L, start, end):
        return sorted(set(range(start, end + 1)).difference(L))


def runGUI():
    global ui
    global app

    app = QtWidgets.QApplication(sys.argv)
    frame = QtWidgets.QFrame()

    ui = Ui_Frame()
    ui.setupUi(frame)
    frame.show()

    sys.exit(app.exec_())


def run(receiver_ip, sender_ip, TCP_port, UDP_port):
    global ui
    global app
    app = QtWidgets.QApplication(sys.argv)
    frame = QtWidgets.QFrame()

    ui = Ui_Frame()
    ui.setupUi(frame)
    frame.show()

    _thread.start_new_thread(ClientSession, (receiver_ip, UDP_port, sender_ip, TCP_port))

    sys.exit(app.exec_())
