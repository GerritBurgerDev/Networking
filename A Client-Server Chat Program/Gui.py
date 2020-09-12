from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *
from socket import AF_INET, socket, SOCK_STREAM

import pickle
import _thread

name_bool = True
connected = False
server_running = True

my_name = " "

ADDR = None
ui = None
Frame = None
client_socket = None

class Communicator(QtCore.QObject):
    message = Signal(object)

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
    def setupUi(self, Frame):
        Frame.setObjectName(_fromUtf8("Frame"))
        Frame.resize(692, 540)
        Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        Frame.setStyleSheet("background-color: #3b3b3b")
        Frame.setFixedSize(QSize(700, 530))

        self.sendButton = QtWidgets.QPushButton(Frame)
        self.sendButton.setGeometry(QtCore.QRect(440, 440, 90, 27))
        self.sendButton.setObjectName(_fromUtf8("sendButton"))
        self.sendButton.clicked.connect(self.send)
        self.sendButton.setStyleSheet(
            "QPushButton { background-color: #b32020; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; } \
             QPushButton:hover { background-color: #942222; } ")

        self.whisperButton = QtWidgets.QPushButton(Frame)
        self.whisperButton.setGeometry(QtCore.QRect(560, 440, 90, 27))
        self.whisperButton.setObjectName(_fromUtf8("WhisperButton"))
        self.whisperButton.setStyleSheet(
            "QPushButton { background-color: #b32020; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; } \
             QPushButton:hover { background-color: #942222; } ")
        self.whisperButton.clicked.connect(self.whisper)

        self.clearButton = QtWidgets.QPushButton(Frame)
        self.clearButton.setGeometry(QtCore.QRect(440, 480, 90, 27))
        self.clearButton.setObjectName(_fromUtf8("clearButton"))
        self.clearButton.clicked.connect(self.clear)
        self.clearButton.setStyleSheet(
            "QPushButton { background-color: #b32020; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; } \
             QPushButton:hover { background-color: #942222; } ")

        self.quitButton = QtWidgets.QPushButton(Frame)
        self.quitButton.setGeometry(QtCore.QRect(560, 480, 90, 27))
        self.quitButton.setObjectName(_fromUtf8("quitButton"))
        self.quitButton.clicked.connect(self.close_window)
        self.quitButton.setStyleSheet(
            "QPushButton { background-color: #b32020; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; } \
             QPushButton:hover { background-color: #942222; } ")

        self.Users = QtWidgets.QFrame(Frame)
        self.Users.setGeometry(QtCore.QRect(430, 10, 251, 391))
        self.Users.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Users.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Users.setObjectName(_fromUtf8("Users"))
        self.Users.setStyleSheet("background-color: #cccccc")

        self.roomLabel = QtWidgets.QLabel(self.Users)
        self.roomLabel.setGeometry(QtCore.QRect(50, 10, 141, 21))

        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Latin Modern Sans Quotation"))
        font.setPointSize(20)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)

        self.roomLabel.setFont(font)
        self.roomLabel.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.roomLabel.setIndent(16)
        self.roomLabel.setObjectName(_fromUtf8("roomLabel"))

        self.showMessages = QtWidgets.QTextEdit(Frame)
        self.showMessages.setGeometry(QtCore.QRect(10, 10, 401, 391))
        self.showMessages.setObjectName(_fromUtf8("showMessages"))
        self.showMessages.setStyleSheet("background-color: #cccccc; \
                                         border-left: 4px solid #b32020; \
                                         padding-left: 4px;")

        self.typeMessage = QtWidgets.QLineEdit(Frame)
        self.typeMessage.setGeometry(QtCore.QRect(10, 440, 401, 71))
        self.typeMessage.setObjectName(_fromUtf8("typeMessage"))
        self.typeMessage.setStyleSheet("border: none; \
                                        border-bottom: 2px solid #b32020; \
                                        background-color: #cccccc;")

        self.scrollable = QtWidgets.QScrollArea(self.Users)
        self.scrollable.setGeometry(0, 40, 251, 391)
        self.listWidget = QtWidgets.QListWidget(self.scrollable)
        self.listWidget.resize(251, 391)

        self.showMessages.raise_()
        self.whisperButton.raise_()
        self.quitButton.raise_()
        self.sendButton.raise_()
        self.clearButton.raise_()
        self.Users.raise_()
        self.typeMessage.raise_()

        self.retranslateUi(Frame)
        self.comm = Communicator()
        self.comm.message.connect(self.receive)

        QtCore.QMetaObject.connectSlotsByName(Frame)

    def close_window(self):
        global app
        import sys

        if server_running == False:
            app.closeAllWindows()
            sys.exit()


        try:
            array = [0,"{quit}"]
            array = pickle.dumps(array)
            array = array.ljust(1024)
            client_socket.send(array)
            app.closeAllWindows()
        except:
            sys.exit()

    def online_users(self, users):
        self.listWidget.clear()
        for user in users:
            item = QtWidgets.QListWidgetItem(self.listWidget)
            item.setText(user)

    def receive(self, msg):
        if msg[0] == "@":
            redText = "<span style=\" color:#8080ff;\" >"
            redText = redText + msg + "</span>"
            self.showMessages.append(redText)

        elif msg[0] == "~":
            blueText = "<span style=\" color:#ff0000;\" >"
            blueText = blueText + msg[1:] + "</span>"
            self.showMessages.append(blueText)

        elif msg[0] == "`":
            greenText = "<span style=\" color:#00b300;\" >"
            greenText = greenText + msg[1:] + "</span>"
            self.showMessages.append(greenText)

        else:
            self.showMessages.append(msg)

    def clear(self):
        self.typeMessage.setText("")

    def send(self):
        global my_name

        if server_running == False:
            return

        text = self.typeMessage.text()

        if text != "":
            array = [1, text, my_name]
            array = pickle.dumps(array)
            array = array.ljust(1024)

            try:
                client_socket.sendall(array)
            except:
                redText = "<span style=\" color:#ff0000;\" >"
                redText = redText + "Server disconnected" + "</span>"
                self.showMessages.append(redText)

        self.typeMessage.setText("")


    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.sendButton.setText(_translate("Frame", "Send", None))
        self.whisperButton.setText(_translate("Frame", "wHiSpA", None))
        self.clearButton.setText(_translate("Frame", "Clear", None))
        self.quitButton.setText(_translate("Frame", "Quit", None))
        self.roomLabel.setText(_translate("Frame", "ROOM", None))

    def whisper(self):
        global my_name

        try:
            to = self.listWidget.currentItem().text()
        except:
            return

        if to == my_name:
            return
        text = self.typeMessage.text()

        if text != "":
            redText = "<span style=\" color:#8080ff;\" >"
            redText = redText + "@" + my_name + ": " + text + "</span>"
            self.showMessages.append(redText)
            array = [69, my_name, to, text]
            client_socket.send(pickle.dumps(array).ljust(1024))

        self.typeMessage.setText("")


class Input(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        global ADDR

        layout = QtWidgets.QFormLayout()
        self.ipLabel = QtWidgets.QLabel()
        self.ipLabel.setText("IP")
        self.portLabel = QtWidgets.QLabel()
        self.portLabel.setText("Port")
        layout.addRow(self.ipLabel, self.portLabel)

        self.ip = QtWidgets.QLineEdit()
        self.ip.setText("146.232.50.156")
        self.port = QtWidgets.QLineEdit()
        self.port.setText("5000")

        layout.addRow(self.ip, self.port)

        self.confirm = QtWidgets.QPushButton()
        self.confirm.setText("Confirm")
        self.confirm.clicked.connect(self.showDialog)
        layout.addRow(self.confirm)

        self.setLayout(layout)

    def showDialog(self):
        global connected
        global client_socket
        global ui
        global Frame

        ADDR = (self.ip.text(), int(self.port.text()))

        client_socket = socket(AF_INET, SOCK_STREAM)

        if connected == False:
            try:
                client_socket.connect(ADDR)
                connected = True
                self.close()
            except:
                connected = False
                print("FAILED TO CONNECT")
                self.window = Input()
                self.show()


        if connected is True:
            self.close()
            msg = client_socket.recv(BUFSIZ)

            text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')

            if ok:
                global my_name
                global name_bool

                my_name = text
                array = [text]
                array = pickle.dumps(array)
                array = array.ljust(1024)
                client_socket.send(array)
                r = client_socket.recv(BUFSIZ)
                r = pickle.loads(r)

                if r[0] == 1:
                    name_bool = False

                while name_bool is True:
                    text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Username in use, enter other username:')

                    my_name = text
                    array = [text]
                    array = pickle.dumps(array)
                    array = array.ljust(1024)
                    client_socket.send(array)
                    r = client_socket.recv(BUFSIZ)
                    r = pickle.loads(r)

                    if r[0] == 1:
                        break

            ui = Ui_Frame()
            ui.setupUi(Frame)
            Frame.show()
            receive_thread = _thread.start_new_thread(receive, ())

BUFSIZ = 1024

def receive():
    global ui
    global server_running

    while True:
        msg = client_socket.recv(BUFSIZ)

        if msg == b'':
            break
        else:
            array = pickle.loads(msg)

            if type(array) == dict:
                ui.online_users(array)

            elif array[0] == 69:
                msg = "@" + array[1] + ": " + array[3]
                ui.comm.message.emit(msg)

            else:
                if len(array) == 1:
                    ui.comm.message.emit(array[0])

                    if array[0] == "~Server disconnected":
                        server_running = False
                        array = [0, "{quit}"]
                        array = pickle.dumps(array)
                        array = array.ljust(1024)
                        client_socket.send(array)
                        break

                else:
                    msg = array[1] + ": " + array[0]
                    ui.comm.message.emit(msg)

app = None
Frame = None

def run():
    global Frame
    global app

    import sys

    app = QtWidgets.QApplication(sys.argv)
    Frame = QtWidgets.QFrame()

    ex = Input()
    ex.show()

    sys.exit(app.exec_())
