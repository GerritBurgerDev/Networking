import _thread
import os
import pickle
import struct
import wave
import time
import mute_alsa
from socket import *
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from threading import Thread

import pyaudio
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import *

# Was the name accepted
name_bool = True

# Was the connection to the server accepted
connected = False

# Client's name
my_name = " "

# Global variables for gui and socket address
ADDR = None
ui = None

client_socket = None

CHOICE = 1

PORT = 5000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Dictionary linking other users in their group and boolean to check whether to receive from them
receivers = {}

# Strores voice notes from users
voicenotes = {}


# Signal Communicator to the GUI
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

    def setupUi(self, Frame):
        # Receive a udp port from the server
        port = client_socket.recv(1024)
        port = pickle.loads(port)
        self.udp_port = port[1]

        # PyAudio initialization
        self.p = pyaudio.PyAudio()

        self.ip = self.get_ip()
        self.channel = "None"
        self.my_name = ""
        self.connected = False
        
        # VOICE NOTES
        self.vn_click = False
        self.recording = False
        self.receiving_vn = True

        # GROUP CALL
        self.running = True
        self.multicasting = False
        self.is_in_group = False
        self.group_name = "None"
        self.users_in_group = []

        # PRIVATE CALL
        self.in_private_call = False

        self.Frame = Frame
        self.Frame.setObjectName(_fromUtf8("Frame"))
        self.Frame.resize(692, 540)
        self.Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Frame.setStyleSheet("background-color: #4a4a4a")
        self.Frame.setFixedSize(QSize(700, 510))

        self.call_button = QtWidgets.QPushButton(self.Frame)
        self.call_button.setGeometry(QtCore.QRect(440, 420, 90, 27))
        self.call_button.setObjectName(_fromUtf8("call_button"))
        self.call_button.clicked.connect(self.call)
        self.call_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                      "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                      "QPushButton:hover { background-color: #942222; }")

        self.whisper_button = QtWidgets.QPushButton(self.Frame)
        self.whisper_button.setGeometry(QtCore.QRect(560, 420, 90, 27))
        self.whisper_button.setObjectName(_fromUtf8("whisper_button"))
        self.whisper_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                      "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                      "QPushButton:hover { background-color: #942222; }")
        self.whisper_button.clicked.connect(self.whisper)

        self.group_call_button = QtWidgets.QPushButton(self.Frame)
        self.group_call_button.setGeometry(QtCore.QRect(440, 460, 90, 27))
        self.group_call_button.setObjectName(_fromUtf8("group_call_button"))
        self.group_call_button.clicked.connect(self.group_call)
        self.group_call_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                      "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                      "QPushButton:hover { background-color: #942222; }")

        self.quit_button = QtWidgets.QPushButton(self.Frame)
        self.quit_button.setGeometry(QtCore.QRect(560, 460, 90, 27))
        self.quit_button.setObjectName(_fromUtf8("quit_button"))
        self.quit_button.clicked.connect(self.close_window)
        self.quit_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                      "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                      "QPushButton:hover { background-color: #942222; }")

        self.Users = QtWidgets.QFrame(self.Frame)
        self.Users.setGeometry(QtCore.QRect(430, 10, 251, 190))
        self.Users.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Users.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Users.setObjectName(_fromUtf8("Users"))
        self.Users.setStyleSheet("background-color: #cccccc;")

        self.Userlist = QtWidgets.QLabel(self.Users)
        self.Userlist.setGeometry(QtCore.QRect(50, 10, 141, 21))

        self.Groups = QtWidgets.QFrame(self.Frame)
        self.Groups.setGeometry(QtCore.QRect(430, 210, 251, 190))
        self.Groups.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Groups.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Groups.setObjectName(_fromUtf8("Groups"))
        self.Groups.setStyleSheet("background-color: #cccccc")

        self.room_label = QtWidgets.QLabel(self.Groups)
        self.room_label.setGeometry(QtCore.QRect(50, 10, 141, 21))

        self.voice_notes = QtWidgets.QFrame(self.Frame)
        self.voice_notes.setGeometry(QtCore.QRect(700, 10, 251, 391))
        self.voice_notes.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.voice_notes.setFrameShadow(QtWidgets.QFrame.Raised)
        self.voice_notes.setObjectName(_fromUtf8("voice_notes"))
        self.voice_notes.setStyleSheet("background-color: #cccccc")

        self.voice_note_list = QtWidgets.QLabel(self.voice_notes)
        self.voice_note_list.setGeometry(QtCore.QRect(10, 10, 215, 21))

        self.group_actions_button = QtWidgets.QPushButton(self.Groups)
        self.group_actions_button.setGeometry(QtCore.QRect(180, 10, 25, 25))
        self.group_actions_button.setIcon(QtGui.QIcon("resources/groups.png"))
        self.group_actions_button.setObjectName(_fromUtf8("group_actions_button"))
        self.group_actions_button.setStyleSheet(
            "QPushButton { background-color: #cccccc; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; border-radius: 4px; } \
             QPushButton:hover { background-color: #ab0909; } ")
        self.group_actions_button.clicked.connect(self.popup_group_actions)

        self.play_vn_button = QtWidgets.QPushButton(self.Frame)
        self.play_vn_button.setGeometry(QtCore.QRect(876, 420, 75, 27))
        self.play_vn_button.setIcon(QtGui.QIcon("resources/play.png"))
        self.play_vn_button.setObjectName(_fromUtf8("play_vn_button"))
        self.play_vn_button.setStyleSheet(
            "QPushButton { background-color: #ab0909; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; border-radius: 4px; } \
             QPushButton:hover { background-color: #942222; } ")
        self.play_vn_button.clicked.connect(self.play_vn_thread)

        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Latin Modern Sans Quotation"))
        font.setPointSize(20)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)

        self.Userlist.setFont(font)
        self.Userlist.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Userlist.setIndent(16)
        self.Userlist.setObjectName(_fromUtf8("Userlist"))

        self.voice_note_list.setFont(font)
        self.voice_note_list.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.voice_note_list.setIndent(16)
        self.voice_note_list.setObjectName(_fromUtf8("voiceNoteList"))

        self.scrollable = QtWidgets.QScrollArea(self.Users)
        self.scrollable.setGeometry(0, 40, 251, 190)
        self.list_widget = QtWidgets.QListWidget(self.scrollable)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget.resize(251, 190)

        self.scrollable_vn = QtWidgets.QScrollArea(self.voice_notes)
        self.scrollable_vn.setGeometry(0, 40, 251, 391)
        self.list_widget_vn = QtWidgets.QListWidget(self.scrollable_vn)
        self.list_widget_vn.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget_vn.resize(251, 391)

        self.room_label.setFont(font)
        self.room_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.room_label.setIndent(16)
        self.room_label.setObjectName(_fromUtf8("room_label"))

        self.scrollable_rooms = QtWidgets.QScrollArea(self.Groups)
        self.scrollable_rooms.setGeometry(0, 40, 251, 190)
        self.list_widget_rooms = QtWidgets.QListWidget(self.scrollable_rooms)
        self.list_widget_rooms.resize(251, 190)

        self.show_messages = QtWidgets.QTextEdit(self.Frame)
        self.show_messages.setGeometry(QtCore.QRect(10, 10, 401, 391))
        self.show_messages.setObjectName(_fromUtf8("show_messages"))
        self.show_messages.setStyleSheet("background-color: #cccccc; \
                                         border-left: 2px solid #ab0909; \
                                         padding-left: 4px; border-radius: 4px;")
        self.show_messages.setReadOnly(True)

        self.voice_notes_button = QtWidgets.QPushButton(self.Frame)
        self.voice_notes_button.setGeometry(QtCore.QRect(375, 20, 25, 25))
        self.voice_notes_button.setIcon(QtGui.QIcon("resources/vn.png"))
        self.voice_notes_button.setObjectName(_fromUtf8("voice_notes_button"))
        self.voice_notes_button.setStyleSheet(
            "QPushButton { background-color: #cccccc; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; border-radius: 4px; } \
             QPushButton:hover { background-color: #ab0909; } ")
        self.voice_notes_button.clicked.connect(self.popup_voice_notes)

        self.type_message = QtWidgets.QTextEdit(self.Frame)
        self.type_message.setGeometry(QtCore.QRect(10, 420, 401, 71))
        self.type_message.setObjectName(_fromUtf8("type_message"))
        self.type_message.setStyleSheet("border: none; \
                                        border-bottom: 2px solid #ab0909; \
                                        background-color: #cccccc; border-radius: 4px;")

        self.record_button = QtWidgets.QPushButton(self.Frame)
        self.record_button.setGeometry(QtCore.QRect(375, 440, 25, 25))
        self.record_button.setIcon(QtGui.QIcon("resources/mic.png"))
        self.record_button.setObjectName(_fromUtf8("record_button"))
        self.record_button.setStyleSheet(
            "QPushButton { background-color: #cccccc; border: 2px solid #942222; color: white; text-align: center; \
            text-decoration: none; font-size: 16px; border-radius: 4px; } \
            QPushButton:hover { background-color: #ab0909; } ")
        self.record_button.clicked.connect(self.record)

        self.show_messages.raise_()
        self.type_message.raise_()
        self.Users.raise_()
        self.whisper_button.raise_()
        self.quit_button.raise_()
        self.call_button.raise_()
        self.group_call_button.raise_()
        self.record_button.raise_()
        self.voice_notes_button.raise_()
        self.group_actions_button.raise_()
        self.play_vn_button.raise_()

        self.retranslateUi(self.Frame)
        self.comm = Communicator()
        self.popup = Communicator()
        self.accept = Communicator()
        self.set_name = Communicator()
        self.start_sending = Communicator()
        self.add_user = Communicator()
        self.set_is_in_group = Communicator()
        self.rooms = Communicator()
        self.set_mult = Communicator()
        self.change_button = Communicator()
        self.change_group_button = Communicator()
        self.popup_vn = Communicator()
        self.comm.message.connect(self.receive)
        self.popup.message.connect(self.receive_call)
        self.accept.message.connect(self.accept_call)
        self.set_name.message.connect(self.name)
        self.start_sending.message.connect(self.send_to_group)
        self.add_user.message.connect(self.add_to_group)
        self.set_is_in_group.message.connect(self.set_in_group)
        self.rooms.message.connect(self.update_rooms)
        self.set_mult.message.connect(self.set_multicasting)
        self.change_button.message.connect(self.change_call_button)
        self.change_group_button.message.connect(self.change_group)
        self.popup_vn.message.connect(self.popup_thread)

        QtCore.QMetaObject.connectSlotsByName(self.Frame)
        self.init_vn()

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.call_button.setText(_translate("Frame", "Call", None))
        self.whisper_button.setText(_translate("Frame", "Send", None))
        self.group_call_button.setText(_translate("Frame", "Group Call", None))
        self.quit_button.setText(_translate("Frame", "Quit", None))
        self.Userlist.setText(_translate("Frame", "Users", None))
        self.room_label.setText(_translate("Frame", "Rooms", None))
        self.record_button.setText(_translate("Frame", "", None))
        self.voice_notes_button.setText(_translate("Frame", "", None))
        self.voice_note_list.setText(_translate("Frame", "Voice Notes", None))
        self.play_vn_button.setText(_translate("Frame", "Play", None))

    def change_call_button(self):
        if self.in_private_call == False:
            self.call_button.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                          "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                          "QPushButton:hover { background-color: #942222; }")
        else:
            self.call_button.setStyleSheet("QPushButton { border-width: 0; outline: none;"
                                          "border-radius: 4px; background-color:  #cccccc; color:  #ecf0f1; }"
                                          "QPushButton:hover { background-color: #942222; }")

    def change_group(self):
        if self.is_in_group == True:
            self.group_call_button.setStyleSheet("QPushButton { border-width: 0; outline: none;"
                                          "border-radius: 4px; background-color:  #cccccc; color:  #ecf0f1; }"
                                          "QPushButton:hover { background-color: #942222; }")
        else:
            self.group_call_button.setStyleSheet("QPushButton { border-width: 0; outline: none;"
                                               "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                               "QPushButton:hover { background-color: #942222; }")

    def play_vn_thread(self):
        selected_vn = self.list_widget_vn.selectedItems()[0].text()
        _thread.start_new_thread(self.play_vn, (selected_vn,))

    def play_vn(self, name):
        frames = voicenotes[name]

        stream_out = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        for frame in frames:
            stream_out.write(frame)

    def popup_thread(self, array):
        self.popup_new_vn(array)

    def popup_new_vn(self, array):
        choice_box = QtWidgets.QMessageBox()
        choice_box.setStyleSheet("background-color: #4a4a4a; color: white;")

        choice_box.setText("You have a new voice note from %s" % (array[0]))
        okButton = QtWidgets.QPushButton()
        okButton.setText('Ok')
        okButton.setStyleSheet(
            "QPushButton { background-color: #ab0909; border: 2px solid #942222; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; } \
             QPushButton:hover { background-color: #942222; } ")

        choice_box.addButton(okButton, QtWidgets.QMessageBox.AcceptRole)

        item = QtWidgets.QListWidgetItem(self.list_widget_vn)
        item.setText(array[1])

        ret = choice_box.exec()

    def popup_voice_notes(self):
        if self.vn_click == False:
            self.vn_click = True
            self.Frame.setFixedSize(QSize(970, 510))
        else:
            self.vn_click = False
            self.Frame.setFixedSize(QSize(700, 510))

    def popup_group_actions(self):
        choice_box = QtWidgets.QMessageBox()
        choice_box.setStyleSheet("background-color: #4a4a4a; color: white;")

        choice_box.setText("Please choose what you want to do:")
        createButton = QtWidgets.QPushButton()
        createButton.setText('Create')
        createButton.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")

        deleteButton = QtWidgets.QPushButton()
        deleteButton.setText('Delete')
        deleteButton.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")

        joinButton = QtWidgets.QPushButton()
        joinButton.setText('Join')
        joinButton.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")

        leaveButton = QtWidgets.QPushButton()
        leaveButton.setText('Leave')
        leaveButton.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")

        cancelButton = QtWidgets.QPushButton()
        cancelButton.setText('Cancel')
        cancelButton.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")

        choice_box.addButton(createButton, QtWidgets.QMessageBox.HelpRole)
        choice_box.addButton(deleteButton, QtWidgets.QMessageBox.ActionRole)
        choice_box.addButton(joinButton, QtWidgets.QMessageBox.ApplyRole)
        choice_box.addButton(leaveButton, QtWidgets.QMessageBox.AcceptRole)
        choice_box.addButton(cancelButton, QtWidgets.QMessageBox.NoRole)

        ret = choice_box.exec()

        if ret == 0:
            self.createGroup()
        elif ret == 1:
            if self.is_in_group == False:
                self.deleteGroup()
            else:
                self.show_messages.append("Please leave your group first")
        elif ret == 2:
            if self.in_private_call == False and self.is_in_group == False:
                self.joinGroup()
            else:
                self.show_messages.append("Please disconnect from your call first")
        elif ret == 3:
            self.leaveGroup()
        else:
            pass

    def createGroup(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')

        if ok:
            name = text

            send = ["create_channel", name, self.ip]
            send = pickle.dumps(send).ljust(1024)
            client_socket.send(send)

    def joinGroup(self):
        try:
            group_name = self.list_widget_rooms.selectedItems()[0]
            group_name = group_name.text()

            send = ["join_channel", group_name, self.ip]
            send = pickle.dumps(send).ljust(1024)
            client_socket.send(send)
        except:
            self.show_messages.append("Please select a channel first")

    def leaveGroup(self):
        try:
            group_name = self.list_widget_rooms.selectedItems()[0]
            group_name = group_name.text()

            self.running = False
            self.is_in_group = False
            self.multicasting = False
            self.users_in_group.clear()

            for ip in receivers:
                receivers[ip] = False

            send = ["leave_channel", group_name, self.ip]
            send = pickle.dumps(send).ljust(1024)
            client_socket.send(send)
        except:
            self.show_messages.append("Please select a channel first")

    def deleteGroup(self):
        try:
            group_name = self.list_widget_rooms.selectedItems()[0]

            if self.in_private_call == False:
                try:
                    group_name = self.list_widget_rooms.selectedItems()[0]
                    group_name = group_name.text()

                    send = ["delete_channel", group_name, self.ip]
                    send = pickle.dumps(send).ljust(1024)
                    client_socket.send(send)
                except:
                    pass
            else:
                self.show_messages.append("You are in a private call and can't do this.")
        except:
            self.show_messages.append("Please select a channel first")

    def record(self):
        if self.recording == False:
            self.recording = True
            _thread.start_new_thread(self.send_vn, ())
        else:
            self.recording = False

    def name(self, name):
        self.my_name = name

    def set_multicasting(self, bool):
        self.multicasting = bool

    def set_in_group(self, bool):
        self.is_in_group = bool

    def get_ip(self):
        gw = os.popen("ip -4 route show default").read().split()
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect((gw[2], 0))
        receiver_ip = s.getsockname()[0]

        return receiver_ip

    def close_window(self):
        global app
        import sys

        try:
            try:
                array = ["{quit}", self.ip]
                array = pickle.dumps(array).ljust(1024)
                client_socket.send(array)
            except:
                pass

            print("QUITTTT")
            self.running = False
            self.multicasting = False
            self.receiving_vn = False

            for ip in receivers:
                receivers[ip] = False

            app.closeAllWindows()
        except:
            sys.exit()
        

    def update_rooms(self, array):
        self.list_widget_rooms.clear()

        if len(array) != 0:
            if array[1] != "0.0.0.0":
                self.multicasting_ip = array[1]

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
            redText = "<span style=\" color:#8080ff;\" >"
            redText = redText + msg + "</span>"
            self.show_messages.append(redText)

        elif msg[0] == "~":
            blueText = "<span style=\" color:#ff0000;\" >"
            blueText = blueText + msg[1:] + "</span>"
            self.show_messages.append(blueText)

        elif msg[0] == "`":
            greenText = "<span style=\" color:black;\" >"
            greenText = greenText + msg[1:] + "</span>"
            self.show_messages.append(greenText)

        else:
            self.show_messages.append(msg)

    def group_call(self):
        if self.is_in_group == False:
            selected_users = self.list_widget.selectedItems()

            if (len(selected_users) == 0) or (len(selected_users) == 1 and selected_users[0].text() == my_name):
                self.show_messages.append("⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣧⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣧⠀⠀⠀⢰⡿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡟⡆⠀⠀⣿⡇⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⣿⠀⢰⣿⡇⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡄⢸⠀⢸⣿⡇⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡇⢸⡄⠸⣿⡇⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⢸⡅⠀⣿⢠⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣥⣾⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⡿⡿⣿⣿⡿⡅⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠉⠀⠉⡙⢔⠛⣟⢋⠦⢵⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⣄⠀⠀⠁⣿⣯⡥⠃⠀⢳⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⡇⠀⠀⠀⠐⠠⠊⢀⠀⢸⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⡿⠀⠀⠀⠀⠀⠈⠁⠀⠀⠘⣿⣄⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⣠⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣷⡀⠀⠀⠀ ⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣧⠀⠀ ⠀⠀⠀⡜⣭⠤⢍⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢛⢭⣗⠀ ⠀⠀⠀⠁⠈⠀⠀⣀⠝⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠠⠀⠀⠰⡅ ⠀⠀⠀⢀⠀⠀⡀⠡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠔⠠⡕⠀ ⠀⠀⠀⠀⣿⣷⣶⠒⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠀⠀⠀⠀ ⠀⠀⠀⠀⠘⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠈⢿⣿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠊⠉⢆⠀⠀⠀⠀ ⠀⢀⠤⠀⠀⢤⣤⣽⣿⣿⣦⣀⢀⡠⢤⡤⠄⠀⠒⠀⠁⠀⠀⠀⢘⠔⠀⠀⠀⠀ ⠀⠀⠀⡐⠈⠁⠈⠛⣛⠿⠟⠑⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⠉⠑⠒⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀")
                self.show_messages.append("Please select at least one person to add to the group call")
                return

            self.is_in_group = True
            self.change_group()
            self.running = True

            if self.in_private_call == False:
                usernames = []

                for item in selected_users:
                    usernames.append(item.text())

                usernames.append(my_name)

                array = ["group_call", usernames, self.my_name]
                client_socket.send(pickle.dumps(array).ljust(1024))
                not_in_list = []

                for user in usernames:
                    if user not in self.users_in_group:
                        not_in_list.append(user)
                        self.users_in_group.append(user)

            else:
                self.users_in_group.clear()
                self.show_messages.append("You are in a private call, you can't begin a group chat now.")

        else:
            self.is_in_group = False
            self.change_group()
            self.running = False

            self.group_call_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                               "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                               "QPushButton:hover { background-color: #942222; }")

            other_persons = self.users_in_group

            for ip in receivers:
                receivers[ip] = False

            send = ["group_disconnect", self.multicasting_ip]
            send = pickle.dumps(send).ljust(1024)
            client_socket.send(send)

            self.users_in_group.clear()

    def add_to_group(self, array):
        ip = array[0]
        mc_ip = array[1]
        self.multicasting_ip = mc_ip
        _thread.start_new_thread(self.cc_recv, (ip, mc_ip,))


    def send_to_group(self, mc_ip):
        self.multicasting_ip = mc_ip
        self.multicasting = True
        # self.group_name = name
        self.is_in_group = True
        _thread.start_new_thread(self.cc_send, (mc_ip,))

    def call(self):
        if self.is_in_group == False:
            if self.in_private_call == False:
                selected_users = self.list_widget.selectedItems()

                if len(selected_users) == 0:
                    self.show_messages.append(
                        "⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣠⣤⣶⣶ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢰⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣀⣀⣾⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿ ⣿⣿⣿⣿⣿⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿ ⣿⣿⣿⣿⣿⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿ ⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿")
                    self.show_messages.append("Please select someone to call")

                elif selected_users[0].text() == my_name:
                    self.show_messages.append("⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣠⣤⣶⣶ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢰⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣀⣀⣾⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿ ⣿⣿⣿⣿⣿⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿ ⣿⣿⣿⣿⣿⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿ ⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿")
                    self.show_messages.append("You can not call yourself")
                if len(selected_users) > 1:
                    self.show_messages.append("Please select only one person")
                elif len(selected_users) == 1:
                    self.call_button.setStyleSheet("QPushButton { border-width: 0; outline: none;"
                                                  "border-radius: 4px; background-color:  #cccccc; color:  #ecf0f1; }"
                                                  "QPushButton:hover { background-color: #942222; }")

                    array = ["call", self.ip, selected_users[0].text()]
                    array = pickle.dumps(array).ljust(1024)
                    client_socket.send(array)

            else:
                self.running = False
                self.in_private_call = False

                self.call_button.setStyleSheet("QPushButton { border-width: 0; outline: none;"
                                              "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                              "QPushButton:hover { background-color: #942222; }")


                other_person = self.users_in_group[0]
                self.users_in_group.clear()

                send = ["call_disconnect", other_person, self.my_name]
                send = pickle.dumps(send).ljust(1024)
                client_socket.send(send)
        else:
            self.show_messages.append("You are in a group call please leave first")

    def whisper(self):
        # global my_name

        try:
            selected_users = self.list_widget.selectedItems()
        except:
            return

        to = []
        for user in selected_users:
            if user.text() == self.my_name:
                self.show_messages.append("⡴⠞⠉⢉⣭⣿⣿⠿⣳⣤⠴⠖⠛⣛⣿⣿⡷⠖⣶⣤⡀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⣼⠁⢀⣶⢻⡟⠿⠋⣴⠿⢻⣧⡴⠟⠋⠿⠛⠠⠾⢛⣵⣿⠀⠀⠀⠀ ⣼⣿⡿⢶⣄⠀⢀⡇⢀⡿⠁⠈⠀⠀⣀⣉⣀⠘⣿⠀⠀⣀⣀⠀⠀⠀⠛⡹⠋⠀⠀⠀⠀ ⣭⣤⡈⢑⣼⣻⣿⣧⡌⠁⠀⢀⣴⠟⠋⠉⠉⠛⣿⣴⠟⠋⠙⠻⣦⡰⣞⠁⢀⣤⣦⣤⠀ ⠀⠀⣰⢫⣾⠋⣽⠟⠑⠛⢠⡟⠁⠀⠀⠀⠀⠀⠈⢻⡄⠀⠀⠀⠘⣷⡈⠻⣍⠤⢤⣌⣀ ⢀⡞⣡⡌⠁⠀⠀⠀⠀⢀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⢿⡀⠀⠀⠀⠸⣇⠀⢾⣷⢤⣬⣉ ⡞⣼⣿⣤⣄⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⣿⠀⠸⣿⣇⠈⠻ ⢰⣿⡿⢹⠃⠀⣠⠤⠶⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⣿⠀⠀⣿⠛⡄⠀ ⠈⠉⠁⠀⠀⠀⡟⡀⠀⠈⡗⠲⠶⠦⢤⣤⣤⣄⣀⣀⣸⣧⣤⣤⠤⠤⣿⣀⡀⠉⣼⡇⠀ ⣿⣴⣴⡆⠀⠀⠻⣄⠀⠀⠡⠀⠀⠀⠈⠛⠋⠀⠀⠀⡈⠀⠻⠟⠀⢀⠋⠉⠙⢷⡿⡇⠀ ⣻⡿⠏⠁⠀⠀⢠⡟⠀⠀⠀⠣⡀⠀⠀⠀⠀⠀⢀⣄⠀⠀⠀⠀⢀⠈⠀⢀⣀⡾⣴⠃⠀ ⢿⠛⠀⠀⠀⠀⢸⠁⠀⠀⠀⠀⠈⠢⠄⣀⠠⠼⣁⠀⡱⠤⠤⠐⠁⠀⠀⣸⠋⢻⡟⠀⠀ ⠈⢧⣀⣤⣶⡄⠘⣆⠀⠀⠀⠀⠀⠀⠀⢀⣤⠖⠛⠻⣄⠀⠀⠀⢀⣠⡾⠋⢀⡞⠀⠀⠀ ⠀⠀⠻⣿⣿⡇⠀⠈⠓⢦⣤⣤⣤⡤⠞⠉⠀⠀⠀⠀⠈⠛⠒⠚⢩⡅⣠⡴⠋⠀⠀⠀⠀ ⠀⠀⠀⠈⠻⢧⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⣻⠿⠋⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠉⠓⠶⣤⣄⣀⡀⠀⠀⠀⠀⠀⢀⣀⣠⡴⠖⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀")
                self.show_messages.append("Nice try")

                return
            else:
                to.append(user.text())

        if len(to) == 0:
            self.show_messages.append("Please select at least one person to send a message to")

        text = self.type_message.toPlainText()

        if text == "":
            self.show_messages.append("Please enter a message to send")

        if text != "":
            redText = "<span style=\" color:#8080ff;\" >"
            redText = redText + "@" + my_name + ": " + text + "</span>"
            self.show_messages.append(redText)
            array = ["message", my_name, to, text]
            client_socket.send(pickle.dumps(array).ljust(1024))

        self.type_message.setText("")

    def send_sound(self, IP_2, port):
        sound = []
        sock_out = socket(AF_INET, SOCK_DGRAM)
        stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        while self.running:
            data = stream.read(CHUNK)
            sound.append(data)
            print(data.__sizeof__())
            sock_out.sendto(data, (IP_2, port))

        wf = wave.open("SENDER.wav", 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(sound))

    def receive_sound(self):
        sound = []
        silence = chr(0)
        stream_out = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

        sock_in = socket(AF_INET, SOCK_DGRAM)
        sock_in.bind((self.ip, self.udp_port))
        sock_in.settimeout(1)

        while self.running:
            try:
                data = sock_in.recv(1057)
                sound.append(data)
            except:
                self.running = False
                self.in_private_call = False
                self.change_call_button()

            stream_out.write(data, exception_on_underflow=False)
            free = stream_out.get_write_available()

            if free > CHUNK:
                to_fill = free - CHUNK
                stream_out.write(silence * to_fill)

        wf = wave.open("RECV.wav", 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(sound))



        print("OUT RECV")

    def cc_send(self, mc_ip):
        MCAST_GRP = mc_ip
        MCAST_PORT = 8005
        MULTICAST_TTL = 2
        stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        sock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, MULTICAST_TTL)

        while self.running:
            data = stream.read(CHUNK)
            sock.sendto(data, (MCAST_GRP, MCAST_PORT))

    def cc_recv(self, l_ip,mc_ip):
        MCAST_GRP = mc_ip
        MCAST_PORT = 8005
        silence = chr(0)

        IS_ALL_GROUPS = True
        stream_out = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
        sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((MCAST_GRP, MCAST_PORT))
        mreq = struct.pack("4sl", inet_aton(MCAST_GRP), INADDR_ANY)
        sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)

        while receivers[l_ip]:
            data, addr = sock.recvfrom(16033)

            if addr[0] == l_ip:
                stream_out.write(data, exception_on_underflow=False)
            free = stream_out.get_write_available()

            if free > CHUNK:
                to_fill = free - CHUNK
                stream_out.write(silence * to_fill)

    def accept_call(self, array):
        self.running = True
        Thread(target=self.send_sound, args=(str(array[1]), array[2],)).start()
        Thread(target=self.receive_sound).start()

    def receive_call(self, array):
        choice_box = QtWidgets.QMessageBox()
        choice_box.setStyleSheet("background-color: #4a4a4a; color: white;")

        choice_box.setText("Incomming call from %s" % (array[1]))
        answer_button = QtWidgets.QPushButton()
        answer_button.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")
        answer_button.setText('Answer')

        decline_button = QtWidgets.QPushButton()
        decline_button.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")
        decline_button.setText('Decline')

        choice_box.addButton(answer_button, QtWidgets.QMessageBox.YesRole)
        choice_box.addButton(decline_button, QtWidgets.QMessageBox.NoRole)

        ret = choice_box.exec()

        if ret == 0:
            self.in_private_call = True
            send = ["receive_call", 1, self.ip, array[1]]
            client_socket.send(pickle.dumps(send).ljust(1024))

            Thread(target=self.send_sound, args=(str(array[2]), array[3],)).start()
            Thread(target=self.receive_sound).start()
        else:
            self.in_private_call = False
            self.change_call_button()
            send = ["receive_call", 0, self.ip, array[1]]
            client_socket.send(pickle.dumps(send).ljust(1024))

    def send_vn(self):
        try:
            selected_users = self.list_widget.selectedItems()
        except:
            pass

        if len(selected_users) == 0:
            self.show_messages.append("⠀⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀ ⠀⠀⠀⣴⠿⠏⠀⠀⠀⠀⠀⠀⢳⡀⠀⡏⠀⠀⠀⠀⠀⢷ ⠀⠀⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀⠀⠀⠀⠀ ⡇ ⠀⠀⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿⠀⣸⠀⠀OK⠀ ⡇ ⠀⠀⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀⠀⣿⠀⢹⠀⠀⠀⠀⠀ ⡇ ⠀⠀⠙⢿⣯⠄⠀⠀⠀⢀⡀⠀⠀⡿⠀⠀⡇⠀⠀⠀⠀⡼ ⠀⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀⠀⠘⠤⣄⣠⠞⠀ ⠀⠀⠀⠀⠀⢸⣷⡦⢤⡤⢤⣞⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⢀⣤⣴⣿⣏⠁⠀⠀⠸⣏⢯⣷⣖⣦⡀⠀⠀⠀⠀⠀⠀ ⢀⣾⣽⣿⣿⣿⣿⠛⢲⣶⣾⢉⡷⣿⣿⠵⣿⠀⠀⠀⠀⠀⠀ ⣼⣿⠍⠉⣿⡭⠉⠙⢺⣇⣼⡏⠀⠀⠀⣄⢸⠀⠀⠀⠀⠀⠀ ⣿⣿⣧⣀⣿.........⣀⣰⣏⣘⣆⣀⠀⠀")
            self.show_messages.append("Please select at least one person to send the voicenote to")

        to = []
        for user in selected_users:
            if user.text() == self.my_name :
                self.show_messages.append("⠀⠀⠀⠀⣠⣶⡾⠏⠉⠙⠳⢦⡀⠀⠀⠀⢠⠞⠉⠙⠲⡀⠀ ⠀⠀⠀⣴⠿⠏⠀⠀⠀⠀⠀⠀⢳⡀⠀⡏⠀⠀⠀⠀⠀⢷ ⠀⠀⢠⣟⣋⡀⢀⣀⣀⡀⠀⣀⡀⣧⠀⢸⠀⠀⠀⠀⠀ ⡇ ⠀⠀⢸⣯⡭⠁⠸⣛⣟⠆⡴⣻⡲⣿⠀⣸⠀⠀OK⠀ ⡇ ⠀⠀⣟⣿⡭⠀⠀⠀⠀⠀⢱⠀⠀⣿⠀⢹⠀⠀⠀⠀⠀ ⡇ ⠀⠀⠙⢿⣯⠄⠀⠀⠀⢀⡀⠀⠀⡿⠀⠀⡇⠀⠀⠀⠀⡼ ⠀⠀⠀⠀⠹⣶⠆⠀⠀⠀⠀⠀⡴⠃⠀⠀⠘⠤⣄⣠⠞⠀ ⠀⠀⠀⠀⠀⢸⣷⡦⢤⡤⢤⣞⣁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⠀⢀⣤⣴⣿⣏⠁⠀⠀⠸⣏⢯⣷⣖⣦⡀⠀⠀⠀⠀⠀⠀ ⢀⣾⣽⣿⣿⣿⣿⠛⢲⣶⣾⢉⡷⣿⣿⠵⣿⠀⠀⠀⠀⠀⠀ ⣼⣿⠍⠉⣿⡭⠉⠙⢺⣇⣼⡏⠀⠀⠀⣄⢸⠀⠀⠀⠀⠀⠀ ⣿⣿⣧⣀⣿.........⣀⣰⣏⣘⣆⣀⠀⠀")
                self.show_messages.append("Please don't send yourself a voicenote")
            else:
                to.append(user.text())

        self.vn_socket.sendto(pickle.dumps(to).ljust(1024), self.vn_send)
        stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        s = []

        while self.recording == True:
            data = stream.read(CHUNK)
            s.append(data)
            self.vn_socket.sendto(data, self.vn_send)

        self.vn_socket.sendto(b'vN_dOnE', self.vn_send)

    def init_vn(self):
        global ADDR
        self.vn_send = ADDR

        self.vn_send = (ADDR[0], self.udp_port + 100)
        self.vn_socket = socket(AF_INET, SOCK_STREAM)
        self.vn_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.vn_socket.connect(self.vn_send)

class Input(QtWidgets.QWidget):
    def __init__(self):
        self.BUFSIZ = 1024
        super().__init__()
        self.initUI()

    def initUI(self):
        global ADDR

        self.setStyleSheet(" background-color: #4a4a4a; color: white; ")

        layout = QtWidgets.QFormLayout()
        self.ipLabel = QtWidgets.QLabel()
        self.ipLabel.setText("IP")
        self.portLabel = QtWidgets.QLabel()
        self.portLabel.setText("Port")
        layout.addRow(self.ipLabel, self.portLabel)

        self.ip = QtWidgets.QLineEdit()
        self.ip.setText("146.232.50.242")
        self.ip.setStyleSheet(" background-color: #cccccc; color: black; ")
        self.port = QtWidgets.QLineEdit()
        self.port.setText("5000")
        self.port.setStyleSheet(" background-color: #cccccc; color: black; ")

        layout.addRow(self.ip, self.port)

        self.confirm = QtWidgets.QPushButton()
        self.confirm.setText("Confirm")
        self.confirm.setStyleSheet("QPushButton { border-width: 0; outline: none; padding: 4px;"
                                   "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                   "QPushButton:hover { background-color: #942222; }")
        self.confirm.clicked.connect(self.showDialog)
        layout.addRow(self.confirm)

        self.setLayout(layout)

    def showDialog(self):
        global connected
        global client_socket
        global ui
        global Frame
        global ADDR

        ADDR = (self.ip.text(), int(self.port.text()))

        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        if connected == False:
            try:
                client_socket.connect(ADDR)
                connected = True
                self.close()
            except:
                connected = False
                self.window = Input()
                self.show()

        if connected is True:
            self.close()

            self.setStyleSheet("QLineEdit { background-color: #cccccc; color: black; } "
                               "QInputDialog { background-color: #4a4a4a; } QLabel { color: white; }"
                               "QPushButton { border-width: 0; outline: none; padding: 4px;"
                               "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                               "QPushButton:hover { background-color: #942222; }")
            text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')

            while text == "":
                text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
                                                          'Username in use or invalid, enter another username:')

            if ok:
                global my_name
                global name_bool

                my_name = text
                array = [text]
                array = pickle.dumps(array)
                array = array.ljust(1024)

                # Send name to server
                client_socket.send(array)

                # Check to see if the name is already taken
                r = client_socket.recv(self.BUFSIZ)
                r = pickle.loads(r)

                # Name is not taken
                if r[0] == 1 and text != "":
                    name_bool = False

                # Name is taken try again
                while name_bool is True:
                    text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
                                                              'Username in use or invalid, enter another username:')

                    while text == "":
                        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
                                                                  'Username in use or invalid, enter another username:')

                    my_name = text
                    array = [text]
                    array = pickle.dumps(array)
                    array = array.ljust(1024)

                    # Send name again
                    client_socket.send(array)

                    # Name taken or not
                    r = client_socket.recv(self.BUFSIZ)
                    r = pickle.loads(r)

                    if r[0] == 1:
                        break

            ui = Ui_Frame()
            ui.setupUi(Frame)
            Frame.show()
            ui.set_name.message.emit(my_name)

            # Start receive thread
            _thread.start_new_thread(receive, ())
            _thread.start_new_thread(receive_vn, ())

        else:
            client_socket.close()
            self.close()
            app.closeAllWindows()

BUFSIZ = 1024

def receive():
    global ui
    global server_running

    while True:
        msg = client_socket.recv(BUFSIZ)

        if msg == b'':
            break
        else:
            try:
                array = pickle.loads(msg)
            except:
                pass

            if type(array) == dict:
                ui.online_users(array)

                if ui.connected == False:
                    array = ["connecting", ui.ip]
                    array = pickle.dumps(array).ljust(1024)
                    client_socket.send(array)

            elif type(array) == list and "224" in array[1]:
                ip = array[1]
                msg = [array[0], "0.0.0.0"]
                ui.rooms.message.emit(msg)

            elif array[0] == "connecting":
                ui.connected = True

                ip = array[2]
                msg = [array[1], ip]
                ui.rooms.message.emit(msg)

            elif array[0] == "reject":
                try:
                    ui.users_in_group.remove(array[2])
                except:
                    pass

                ui.comm.message.emit(array[1])

            elif array[0] == "group_call":
                ui.comm.message.emit("You have been added to a conference call")

                if ui.in_private_call == True:
                    msg = ["reject", "%s is in a private call" % ui.my_name, array[3], ui.my_name]
                    msg = pickle.dumps(msg).ljust(1024)
                    client_socket.send(msg)

                else:
                    ui.is_in_group = True
                    ui.set_is_in_group.message.emit(True)
                    ui.running = True
                    ui.change_group_button.message.emit(True)
                    mc_ip = array[2]

                    for u in array[1]:
                        if u == ui.ip:
                            ui.start_sending.message.emit(mc_ip)
                        else:
                            array = [u, mc_ip]
                            receivers[u] = True
                            ui.add_user.message.emit(array)

            elif array[0] == "call_accepted":
                ui.comm.message.emit("Your call was accepted")
                ui.in_private_call = True
                emit = [0, array[1], array[2]]
                ui.users_in_group.append(array[1])
                ui.accept.message.emit(emit)

            elif array[0] == "call_rejected":
                ui.comm.message.emit("Your call was rejected")
                ui.in_private_call = False
                ui.change_button.message.emit(True)

            elif array[0] == "receive_call":
                if ui.in_private_call == True:
                    msg = ["reject", "Already in a private call", array[2]]
                    msg = pickle.dumps(msg).ljust(1024)
                    client_socket.send(msg)
                else:
                    if array[2] != ui.ip:
                        emit_list = [0, array[1], array[2], array[3]]
                        ui.users_in_group.append(array[2])
                        ui.running = True
                        ui.in_private_call = True
                        ui.popup.message.emit(emit_list)
                        ui.change_button.message.emit(True)
                    else:
                        ui.change_button.message.emit(True)

            elif array[0] == "message":
                msg = "`" + array[1] + ": " + array[3]
                ui.comm.message.emit(msg)

            elif array[0] == "create_channel":
                if array[1] == "name_taken":
                    ui.comm.message.emit("This channel already exists.")
                elif array[1] == "great_success":
                    ip = array[3]
                    msg = [array[2], "0.0.0.0"]
                    ui.comm.message.emit("You have created a channel")
                    ui.rooms.message.emit(msg)

            elif array[0] == "join_channel":
                ui.running = True
                ips = array[1]
                names = array[3]
                mc_ip = array[4]
                channel = array[2]

                ui.comm.message.emit("You have joined the channel %s" % (array[2]))

                for ip in ips:
                    if ip == ui.ip:
                        if ui.multicasting == False:
                            ui.start_sending.message.emit(mc_ip)
                            ui.multicasting = True
                            ui.is_in_group = True
                            ui.running = True
                            ui.set_mult.message.emit(True)
                            ui.multicasting_ip = mc_ip
                            ui.channel = channel
                    else:
                        receivers[ip] = True
                        array = [ip, mc_ip]
                        ui.add_user.message.emit(array)

            elif array[0] == "delete_channel":
                ui.comm.message.emit("You have deleted a channel")

                if ui.channel == array[2]:
                    ui.running = False
                    ui.is_in_group = False
                    ui.set_mult.message.emit(False)
                    ui.users_in_group.clear()

                    for ip in receivers:
                        receivers[ip] = False

                if ui.is_in_group == False:
                    ui.running = False
                    ui.is_in_group = False
                    ui.set_mult.message.emit(False)
                    ui.users_in_group.clear()

                    for ip in receivers:
                        receivers[ip] = False

                msg = [array[1], "0.0.0.0"]
                ui.rooms.message.emit(msg)

            elif array[0] == "leave_channel":
                receivers[array[1]] = False

            elif array[0] == "leave_channel_self":
                ui.running = False
                ui.is_in_group = False
                ui.set_mult.message.emit(False)
                ui.users_in_group.clear()

                for r in receivers:
                    r = False

            elif array[0] == "call_disconnect":
                ui.running = False
                ui.in_private_call = False
                ui.change_button.message.emit(True)
                ui.users_in_group.clear()

            elif array[0] == "group_disconnect":
                ui.running = False
                ui.is_in_group = False
                ui.set_mult.message.emit(False)
                ui.change_group_button.message.emit(True)
                ui.users_in_group.clear()

                for r in receivers:
                    r = False

            elif array[0] == "server_quit":
                msg = "~Server has disconnected, bye Felicia"
                ui.comm.message.emit(msg)
                time.sleep(3)
                ui.close_window()
            else:
                pass

def receive_vn():
    global ADDR
    global ui

    # addr = ADDR
    addr = (ADDR[0], ui.udp_port + 200)
    vn_socket = socket(AF_INET, SOCK_STREAM)
    vn_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    vn_socket.connect(addr)
    num = 1

    while ui.receiving_vn:
        frames = []
        sender_name = vn_socket.recv(1024)

        try:
            sender_name = pickle.loads(sender_name)
        except:
            pass

        time.sleep(0.0001)
        data = vn_socket.recv(1024)

        while data != b'vN_dOnE':
            time.sleep(0.0001)
            frames.append(data)
            data = vn_socket.recv(1024)


        write = sender_name[0] + "_" + str(num) + ".wav"
        voicenotes[write] = frames

        array = [sender_name[0], write]
        ui.popup_vn.message.emit(array)
        num += 1


if __name__ == '__main__':
    global Frame
    global app

    import sys

    app = QtWidgets.QApplication(sys.argv)
    Frame = QtWidgets.QFrame()

    ex = Input()
    ex.show()

    sys.exit(app.exec_())
