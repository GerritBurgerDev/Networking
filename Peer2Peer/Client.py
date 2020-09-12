import _thread
import os
import ssl
import pickle
from socket import *
from PySide2 import QtCore, QtGui, QtWidgets
import time
import threading
from PySide2.QtCore import *
import SearchTester as ST

# Was the name accepted
name_bool = True
recv = []

# Was the connection to the server accepted
connected = False
uploading = False
uploading2 = False

# Client's name
my_name = " "

# Global variables for gui and socket address
ADDR = None
ui = None

client_socket = None


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
        self.ip = self.get_ip()
        self.my_name = ""
        self.connected = False
        self.dl_class = None
        self.ul_class = None

        self.files_click = False
        self.downloading = False
        self.uploading = False

        self.sender_ip = ""
        self.dl_running = False
        self.dl_amount = 0
        self.set_port = 0
        self.file_name = ""

        self.search_results = []

        self.Frame = Frame
        self.Frame.setObjectName(_fromUtf8("Frame"))
        self.Frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.Frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.Frame.setStyleSheet("background-color: #4a4a4a")
        self.Frame.setFixedSize(QSize(970, 510))

        self.whisper_button = QtWidgets.QPushButton(self.Frame)
        self.whisper_button.setGeometry(QtCore.QRect(430, 470, 90, 27))
        self.whisper_button.setObjectName(_fromUtf8("whisper_button"))
        self.whisper_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                          "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                          "QPushButton:hover { background-color: #942222; }")
        self.whisper_button.clicked.connect(self.whisper)

        self.quit_button = QtWidgets.QPushButton(self.Frame)
        self.quit_button.setGeometry(QtCore.QRect(590, 470, 90, 27))
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

        self.search_label = QtWidgets.QLabel(self.Frame)
        self.search_label.setGeometry(QtCore.QRect(430, 210, 251, 30))
        self.search_label.setText("Search for a file:")
        self.search_label.setStyleSheet("color: #cccccc")

        self.search_button = QtWidgets.QPushButton(self.Frame)
        self.search_button.setGeometry(QtCore.QRect(590, 275, 90, 27))
        self.search_button.setObjectName(_fromUtf8("Search"))
        self.search_button.clicked.connect(self.search)
        self.search_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                         "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                         "QPushButton:hover { background-color: #942222; }")

        self.search_box = QtWidgets.QLineEdit(self.Frame)
        self.search_box.setGeometry(QtCore.QRect(430, 240, 251, 30))
        self.search_box.setStyleSheet("background-color: #cccccc")

        self.files = QtWidgets.QFrame(self.Frame)
        self.files.setGeometry(QtCore.QRect(700, 10, 251, 391))
        self.files.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.files.setFrameShadow(QtWidgets.QFrame.Raised)
        self.files.setObjectName(_fromUtf8("Files"))
        self.files.setStyleSheet("background-color: #cccccc")

        self.files_list = QtWidgets.QLabel(self.files)
        self.files_list.setGeometry(QtCore.QRect(65, 10, 215, 21))

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

        self.files_list.setFont(font)
        self.files_list.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.files_list.setIndent(16)
        self.files_list.setObjectName(_fromUtf8("files_list"))

        self.download_button = QtWidgets.QPushButton(self.Frame)
        self.download_button.setGeometry(QtCore.QRect(862, 420, 90, 27))
        self.download_button.setObjectName(_fromUtf8("download_button"))
        self.download_button.setStyleSheet(
            "QPushButton { background-color: #ab0909; color: white; text-align: center; \
                                      text-decoration: none; font-size: 16px; border-radius: 4px; } \
             QPushButton:hover { background-color: #942222; } ")
        self.download_button.clicked.connect(self.download)

        self.scrollable = QtWidgets.QScrollArea(self.Users)
        self.scrollable.setGeometry(0, 40, 251, 190)
        self.list_widget = QtWidgets.QListWidget(self.scrollable)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget.resize(251, 190)

        self.scrollable_files = QtWidgets.QScrollArea(self.files)
        self.scrollable_files.setGeometry(0, 40, 251, 391)
        self.list_widget_files = QtWidgets.QListWidget(self.scrollable_files)
        self.list_widget_files.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.list_widget_files.resize(251, 391)

        self.show_messages = QtWidgets.QTextEdit(self.Frame)
        self.show_messages.setGeometry(QtCore.QRect(10, 10, 401, 391))
        self.show_messages.setObjectName(_fromUtf8("show_messages"))
        self.show_messages.setStyleSheet("background-color: #cccccc; \
                                         border-left: 2px solid #ab0909; \
                                         padding-left: 4px; border-radius: 4px;")
        self.show_messages.setReadOnly(True)

        self.type_message = QtWidgets.QTextEdit(self.Frame)
        self.type_message.setGeometry(QtCore.QRect(10, 430, 401, 71))
        self.type_message.setObjectName(_fromUtf8("type_message"))
        self.type_message.setStyleSheet("border: none; \
                                        border-bottom: 2px solid #ab0909; \
                                        background-color: #cccccc; border-radius: 4px;")

        self.upload_label = QtWidgets.QLabel(self.Frame)
        self.upload_label.setGeometry(QtCore.QRect(430, 280, 150, 30))
        self.upload_label.setText("Upload:")
        self.upload_label.setStyleSheet("color: #cccccc")

        self.progress_bar = QtWidgets.QProgressBar(self.Frame)
        self.progress_bar.setGeometry(QtCore.QRect(430, 310, 251, 30))
        self.progress_bar.setStyleSheet("background-color: #cccccc")
        self.progress_bar.setValue(0)

        self.pause_button = QtWidgets.QPushButton(self.Frame)
        self.pause_button.setGeometry(QtCore.QRect(590, 345, 90, 27))
        self.pause_button.setObjectName(_fromUtf8("pause_button"))
        self.pause_button.clicked.connect(self.pause_ul)
        self.pause_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                        "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                        "QPushButton:hover { background-color: #942222; }")

        self.continue_button = QtWidgets.QPushButton(self.Frame)
        self.continue_button.setGeometry(QtCore.QRect(430, 345, 90, 27))
        self.continue_button.setObjectName(_fromUtf8("continue_button"))
        self.continue_button.clicked.connect(self.god_speed_ul)
        self.continue_button.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                           "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                           "QPushButton:hover { background-color: #942222; }")

        self.dl_label = QtWidgets.QLabel(self.Frame)
        self.dl_label.setGeometry(QtCore.QRect(430, 375, 150, 20))
        self.dl_label.setText("Download:")
        self.dl_label.setStyleSheet("color: #cccccc")

        self.progress_bar_dl = QtWidgets.QProgressBar(self.Frame)
        self.progress_bar_dl.setGeometry(QtCore.QRect(430, 400, 251, 30))
        self.progress_bar_dl.setStyleSheet("background-color: #cccccc")
        self.progress_bar_dl.setValue(0)

        self.pause_button_dl = QtWidgets.QPushButton(self.Frame)
        self.pause_button_dl.setGeometry(QtCore.QRect(590, 435, 90, 27))
        self.pause_button_dl.setObjectName(_fromUtf8("pause_button_dl"))
        self.pause_button_dl.clicked.connect(self.pause_dl)
        self.pause_button_dl.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                           "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                           "QPushButton:hover { background-color: #942222; }")

        self.continue_button_dl = QtWidgets.QPushButton(self.Frame)
        self.continue_button_dl.setGeometry(QtCore.QRect(430, 435, 90, 27))
        self.continue_button_dl.setObjectName(_fromUtf8("continue_button"))
        self.continue_button_dl.clicked.connect(self.god_speed_dl)
        self.continue_button_dl.setStyleSheet("QPushButton { border-width: 0; outline: none; "
                                              "border-radius: 4px; background-color:  #ab0909; color:  #ecf0f1; }"
                                              "QPushButton:hover { background-color: #942222; }")

        self.show_messages.raise_()
        self.type_message.raise_()
        self.Users.raise_()
        self.whisper_button.raise_()
        self.quit_button.raise_()
        self.search_button.raise_()

        self.retranslateUi(self.Frame)
        self.comm = Communicator()
        self.rooms = Communicator()
        self.set_name = Communicator()
        self.get_search = Communicator()
        self.d_button = Communicator()
        self.set_value = Communicator()
        self.set_value_dl = Communicator()
        self.comm.message.connect(self.receive)
        self.set_name.message.connect(self.name)
        self.get_search.message.connect(self.search_files)
        self.d_button.message.connect(self.disable_button)
        self.set_value.message.connect(self.change_value)
        self.set_value_dl.message.connect(self.change_value_dl)

        QtCore.QMetaObject.connectSlotsByName(self.Frame)

    def retranslateUi(self, Frame):
        Frame.setWindowTitle(_translate("Frame", "Frame", None))
        self.whisper_button.setText(_translate("Frame", "Send", None))
        self.quit_button.setText(_translate("Frame", "Quit", None))
        self.Userlist.setText(_translate("Frame", "Users", None))
        self.search_button.setText(_translate("Frame", "Search", None))
        self.files_list.setText(_translate("Frame", "Files", None))
        self.download_button.setText(_translate("Frame", "Download", None))
        self.pause_button.setText(_translate("Frame", "Pause", None))
        self.continue_button.setText(_translate("Frame", "God Speed", None))
        self.pause_button_dl.setText(_translate("Frame", "Pause", None))
        self.continue_button_dl.setText(_translate("Frame", "God Speed", None))

    def pause_dl(self):
        if self.dl_running == False:
            self.show_messages.append(
                "⣿⣿⡿⠟⠛⠛⣿⠛⠛⠛⠛⢻⠛⠛⠛⢻⡟⠛⣿⣿⠛⢻⣿⣿⣿⣿⣿⣿ ⣿⣿⡇⠐⠿⣿⣿⣿⡇⢸⣿⣿⠄⢸⣿⣿⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣶⣤⠈⣿⣿⡇⢸⣿⣿⠄⢰⣶⣾⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣇⣉⣁⣤⣿⣿⣇⣸⣿⣿⣀⣸⣿⣿⣿⣤⣈⣁⣤⣿⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ ⡿⢿⣿⡿⠿⣿⡿⢿⡿⠿⠿⠿⣿⡿⠿⠿⠿⣿⠿⠿⠿⠿⣿⣿⠿⠟⠿⣿ ⡇⠈⣿⠄⠄⣿⠃⣸⡇⠄⣶⣶⣿⡇⢰⣶⣶⣿⠄⢸⡷⠄⣿⡇⠰⢿⣶⣿ ⣿⠄⠋⢰⡆⠸⠄⣿⡇⠄⣤⣤⣿⡇⢠⣤⣤⣿⠄⢰⣤⠈⢻⣿⣦⣄⠈⢿ ⣿⣇⣀⣾⣷⣀⣸⣿⣇⣀⣉⣉⣹⣇⣈⣉⣉⣿⣀⣈⣉⣠⣾⣋⣉⣉⣠⣿")
            self.show_messages.append("You can not pause, no downloads running.")
            return

        self.dl_running = False

        arr = ["pause_dl", self.sender_ip]
        client_socket.send(pickle.dumps(arr).ljust(1024))

    def pause_ul(self):
        global uploading2
        global uploading
        if uploading == False:
            self.show_messages.append(
                "⣿⣿⡿⠟⠛⠛⣿⠛⠛⠛⠛⢻⠛⠛⠛⢻⡟⠛⣿⣿⠛⢻⣿⣿⣿⣿⣿⣿ ⣿⣿⡇⠐⠿⣿⣿⣿⡇⢸⣿⣿⠄⢸⣿⣿⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣶⣤⠈⣿⣿⡇⢸⣿⣿⠄⢰⣶⣾⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣇⣉⣁⣤⣿⣿⣇⣸⣿⣿⣀⣸⣿⣿⣿⣤⣈⣁⣤⣿⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ ⡿⢿⣿⡿⠿⣿⡿⢿⡿⠿⠿⠿⣿⡿⠿⠿⠿⣿⠿⠿⠿⠿⣿⣿⠿⠟⠿⣿ ⡇⠈⣿⠄⠄⣿⠃⣸⡇⠄⣶⣶⣿⡇⢰⣶⣶⣿⠄⢸⡷⠄⣿⡇⠰⢿⣶⣿ ⣿⠄⠋⢰⡆⠸⠄⣿⡇⠄⣤⣤⣿⡇⢠⣤⣤⣿⠄⢰⣤⠈⢻⣿⣦⣄⠈⢿ ⣿⣇⣀⣾⣷⣀⣸⣿⣇⣀⣉⣉⣹⣇⣈⣉⣉⣿⣀⣈⣉⣠⣾⣋⣉⣉⣠⣿")
            self.show_messages.append("You can not pause, no uploads running.")
            return

        uploading2 = True

    def god_speed_ul(self):
        global uploading2
        global uploading

        if uploading == False:
            self.show_messages.append(
                "⣿⣿⡿⠟⠛⠛⣿⠛⠛⠛⠛⢻⠛⠛⠛⢻⡟⠛⣿⣿⠛⢻⣿⣿⣿⣿⣿⣿ ⣿⣿⡇⠐⠿⣿⣿⣿⡇⢸⣿⣿⠄⢸⣿⣿⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣶⣤⠈⣿⣿⡇⢸⣿⣿⠄⢰⣶⣾⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣇⣉⣁⣤⣿⣿⣇⣸⣿⣿⣀⣸⣿⣿⣿⣤⣈⣁⣤⣿⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ ⡿⢿⣿⡿⠿⣿⡿⢿⡿⠿⠿⠿⣿⡿⠿⠿⠿⣿⠿⠿⠿⠿⣿⣿⠿⠟⠿⣿ ⡇⠈⣿⠄⠄⣿⠃⣸⡇⠄⣶⣶⣿⡇⢰⣶⣶⣿⠄⢸⡷⠄⣿⡇⠰⢿⣶⣿ ⣿⠄⠋⢰⡆⠸⠄⣿⡇⠄⣤⣤⣿⡇⢠⣤⣤⣿⠄⢰⣤⠈⢻⣿⣦⣄⠈⢿ ⣿⣇⣀⣾⣷⣀⣸⣿⣇⣀⣉⣉⣹⣇⣈⣉⣉⣿⣀⣈⣉⣠⣾⣋⣉⣉⣠⣿")
            self.show_messages.append("You can not resume , no uploads running.")
            return

        uploading2 = False

    def god_speed_dl(self):
        if self.dl_running == True or self.file_name == "":
            self.show_messages.append(
                "⣿⣿⡿⠟⠛⠛⣿⠛⠛⠛⠛⢻⠛⠛⠛⢻⡟⠛⣿⣿⠛⢻⣿⣿⣿⣿⣿⣿ ⣿⣿⡇⠐⠿⣿⣿⣿⡇⢸⣿⣿⠄⢸⣿⣿⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣶⣤⠈⣿⣿⡇⢸⣿⣿⠄⢰⣶⣾⡇⠄⣿⣿⠄⢸⣿⣿⣿⣿⣿⣿ ⣿⣿⣇⣉⣁⣤⣿⣿⣇⣸⣿⣿⣀⣸⣿⣿⣿⣤⣈⣁⣤⣿⣿⣿⣿⣿⣿⣿ ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ ⡿⢿⣿⡿⠿⣿⡿⢿⡿⠿⠿⠿⣿⡿⠿⠿⠿⣿⠿⠿⠿⠿⣿⣿⠿⠟⠿⣿ ⡇⠈⣿⠄⠄⣿⠃⣸⡇⠄⣶⣶⣿⡇⢰⣶⣶⣿⠄⢸⡷⠄⣿⡇⠰⢿⣶⣿ ⣿⠄⠋⢰⡆⠸⠄⣿⡇⠄⣤⣤⣿⡇⢠⣤⣤⣿⠄⢰⣤⠈⢻⣿⣦⣄⠈⢿ ⣿⣇⣀⣾⣷⣀⣸⣿⣇⣀⣉⣉⣹⣇⣈⣉⣉⣿⣀⣈⣉⣠⣾⣋⣉⣉⣠⣿")
            self.show_messages.append("You can not resume , no downloads running.")
            return

        self.dl_amount = os.path.getsize("Downloads/" + self.file_name)

        arr = ["resume_dl", self.ip, self.set_port, self.file_name, self.dl_amount, self.sender_ip]
        client_socket.send(pickle.dumps(arr).ljust(1024))

    def change_value(self, value):
        self.progress_bar.setValue(value)

    def change_value_dl(self, value):
        self.progress_bar_dl.setValue(value)

    def disable_button(self):
        if self.downloading == True:
            self.download_button.setStyleSheet(
                "QPushButton { background-color: #ab0909; color: white; text-align: center; \
                                          text-decoration: none; font-size: 16px; border-radius: 4px; } \
                 QPushButton:hover { background-color: #942222; } ")

            self.downloading = False
        else:
            self.download_button.setStyleSheet(
                "QPushButton { background-color: #cccccc; color: white; text-align: center; \
                                          text-decoration: none; font-size: 16px; border-radius: 4px; } \
                 QPushButton:hover { background-color: #942222; } ")

            self.downloading = True

    def download(self):
        if len(self.list_widget_files.selectedItems()) == 0:
            ui.comm.message.emit("Please select a file to download")
            return

        if self.downloading == False:
            selected_file = self.list_widget_files.selectedItems()[0].text()
            splice = selected_file.split(" ~ ")
            self.file_name = splice[0]
            arr = ["download", "Files/" + splice[0], splice[1], self.my_name]

            client_socket.send(pickle.dumps(arr).ljust(1024))

            self.download_button.setStyleSheet(
                "QPushButton { background-color: #cccccc; color: white; text-align: center; \
                                          text-decoration: none; font-size: 16px; border-radius: 4px; } \
                 QPushButton:hover { background-color: #942222; } ")

            self.downloading = True
            self.dl_running = True

    def search_files(self, results):
        for file in results[0]:
            item = QtWidgets.QListWidgetItem(self.list_widget_files)
            item.setText(file + " ~ " + results[1])

    def search(self):
        self.list_widget_files.clear()
        param = self.search_box.text()

        if param != "":
            array = ["search", param, self.my_name]
            array = pickle.dumps(array).ljust(1024)
            client_socket.send(array)

        else:
            self.show_messages.append("Please specify a search query first.")

        self.search_box.clear()

    def name(self, name):
        self.my_name = name

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

            self.running = False

            app.closeAllWindows()
        except:
            sys.exit()

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

    def whisper(self):

        try:
            selected_users = self.list_widget.selectedItems()
        except:
            return

        to = []
        for user in selected_users:
            if user.text() == self.my_name:
                self.show_messages.append(
                    "⡴⠞⠉⢉⣭⣿⣿⠿⣳⣤⠴⠖⠛⣛⣿⣿⡷⠖⣶⣤⡀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠀⣼⠁⢀⣶⢻⡟⠿⠋⣴⠿⢻⣧⡴⠟⠋⠿⠛⠠⠾⢛⣵⣿⠀⠀⠀⠀ ⣼⣿⡿⢶⣄⠀⢀⡇⢀⡿⠁⠈⠀⠀⣀⣉⣀⠘⣿⠀⠀⣀⣀⠀⠀⠀⠛⡹⠋⠀⠀⠀⠀ ⣭⣤⡈⢑⣼⣻⣿⣧⡌⠁⠀⢀⣴⠟⠋⠉⠉⠛⣿⣴⠟⠋⠙⠻⣦⡰⣞⠁⢀⣤⣦⣤⠀ ⠀⠀⣰⢫⣾⠋⣽⠟⠑⠛⢠⡟⠁⠀⠀⠀⠀⠀⠈⢻⡄⠀⠀⠀⠘⣷⡈⠻⣍⠤⢤⣌⣀ ⢀⡞⣡⡌⠁⠀⠀⠀⠀⢀⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⢿⡀⠀⠀⠀⠸⣇⠀⢾⣷⢤⣬⣉ ⡞⣼⣿⣤⣄⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⣿⠀⠸⣿⣇⠈⠻ ⢰⣿⡿⢹⠃⠀⣠⠤⠶⣼⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⣿⠀⠀⣿⠛⡄⠀ ⠈⠉⠁⠀⠀⠀⡟⡀⠀⠈⡗⠲⠶⠦⢤⣤⣤⣄⣀⣀⣸⣧⣤⣤⠤⠤⣿⣀⡀⠉⣼⡇⠀ ⣿⣴⣴⡆⠀⠀⠻⣄⠀⠀⠡⠀⠀⠀⠈⠛⠋⠀⠀⠀⡈⠀⠻⠟⠀⢀⠋⠉⠙⢷⡿⡇⠀ ⣻⡿⠏⠁⠀⠀⢠⡟⠀⠀⠀⠣⡀⠀⠀⠀⠀⠀⢀⣄⠀⠀⠀⠀⢀⠈⠀⢀⣀⡾⣴⠃⠀ ⢿⠛⠀⠀⠀⠀⢸⠁⠀⠀⠀⠀⠈⠢⠄⣀⠠⠼⣁⠀⡱⠤⠤⠐⠁⠀⠀⣸⠋⢻⡟⠀⠀ ⠈⢧⣀⣤⣶⡄⠘⣆⠀⠀⠀⠀⠀⠀⠀⢀⣤⠖⠛⠻⣄⠀⠀⠀⢀⣠⡾⠋⢀⡞⠀⠀⠀ ⠀⠀⠻⣿⣿⡇⠀⠈⠓⢦⣤⣤⣤⡤⠞⠉⠀⠀⠀⠀⠈⠛⠒⠚⢩⡅⣠⡴⠋⠀⠀⠀⠀ ⠀⠀⠀⠈⠻⢧⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⣻⠿⠋⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀⠉⠓⠶⣤⣄⣀⡀⠀⠀⠀⠀⠀⢀⣀⣠⡴⠖⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀")
                self.show_messages.append("Nice try")

                return
            else:
                to.append(user.text())

        if len(to) == 0:
            to.append("ev")

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
        self.ip.setText("146.232.51.14")
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
        original_socket = socket(AF_INET, SOCK_STREAM)
        original_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sslContext.set_ciphers(
            "NULL-SHA256 AES128-SHA256 AES256-SHA256 AES128-GCM-SHA256 AES256-GCM-SHA384 DH-RSA-AES128-SHA256 DH-RSA-AES256-SHA256 DH-RSA-AES128-GCM-SHA256 DH-RSA-AES256-GCM-SHA384 DH-DSS-AES128-SHA256 DH-DSS-AES256-SHA256 DH-DSS-AES128-GCM-SHA256 DH-DSS-AES256-GCM-SHA384 DHE-RSA-AES128-SHA256 DHE-RSA-AES256-SHA256 DHE-RSA-AES128-GCM-SHA256 DHE-RSA-AES256-GCM-SHA384 DHE-DSS-AES128-SHA256 DHE-DSS-AES256-SHA256 DHE-DSS-AES128-GCM-SHA256 DHE-DSS-AES256-GCM-SHA384 ECDHE-RSA-AES128-SHA256 ECDHE-RSA-AES256-SHA384 ECDHE-RSA-AES128-GCM-SHA256 ECDHE-RSA-AES256-GCM-SHA384 ECDHE-ECDSA-AES128-SHA256 ECDHE-ECDSA-AES256-SHA384 ECDHE-ECDSA-AES128-GCM-SHA256 ECDHE-ECDSA-AES256-GCM-SHA384 ADH-AES128-SHA256 ADH-AES256-SHA256 ADH-AES128-GCM-SHA256 ADH-AES256-GCM-SHA384 AES128-CCM AES256-CCM DHE-RSA-AES128-CCM DHE-RSA-AES256-CCM AES128-CCM8 AES256-CCM8 DHE-RSA-AES128-CCM8 DHE-RSA-AES256-CCM8 ECDHE-ECDSA-AES128-CCM ECDHE-ECDSA-AES256-CCM ECDHE-ECDSA-AES128-CCM8 ECDHE-ECDSA-AES256-CCM8")
        sslContext.load_dh_params("dhparam.pem")
        client_socket = sslContext.wrap_socket(original_socket, server_side=False, )

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

            if ok:
                global my_name
                global name_bool

                while text == "":
                    text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog',
                                                              'Username in use or invalid, enter another username:')

                    if ok:
                        if text != "":
                            break
                    else:
                        client_socket.close()
                        self.close()
                        app.closeAllWindows()
                        return

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

                        if ok:
                            if text != "":
                                break
                        else:
                            client_socket.close()
                            self.close()
                            app.closeAllWindows()
                            return

                    if text != "":
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

            else:
                client_socket.close()
                self.close()
                app.closeAllWindows()


BUFSIZ = 1024


def receive():
    global ui
    global uploading
    global uploading2
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

            elif array[0] == "message":
                msg = "`" + array[1] + ": " + array[3]
                ui.comm.message.emit(msg)

            elif array[0] == "search":
                results = ST.search(array[1])
                other_user = array[2]

                arr = ["results", results, other_user]
                arr = pickle.dumps(arr).ljust(1024)
                client_socket.send(arr)

            elif array[0] == "search_results":
                if len(array[1]) == 0:
                    msg = "`" + "No files were found from " + array[2]
                    ui.comm.message.emit(msg)
                else:
                    results = [array[1], array[2]]
                    ui.get_search.message.emit(results)

            elif array[0] == "upload":
                if uploading == False:
                    arr = ["accept_upload", array[1], array[2], array[3]]
                    client_socket.send(pickle.dumps(arr).ljust(1024))
                    uploading = True

                    _thread.start_new_thread(ul_socket, (array[2], 0, array[3], array[1]))
                else:
                    arr = ["busy_uploading", array[1], array[3], ui.my_name]
                    client_socket.send(pickle.dumps(arr).ljust(1024))

            elif array[0] == "accept_upload":
                ui.sender_ip = array[3]
                ui.set_port = array[1]
                _thread.start_new_thread(dl_socket_class, (array[1],))

            elif array[0] == "busy_uploading":
                ui.comm.message.emit("Client is busy uploading, please wait.")

            elif array[0] == "pause_ul":
                uploading = False

            elif array[0] == "resume_ul":
                uploading = True
                _thread.start_new_thread(ul_socket, ('Files/' + array[2], array[3], array[1], array[4]))

            elif array[0] == "resume_dl":
                ui.dl_running = True
                _thread.start_new_thread(dl_socket_class, (array[1],))

            elif array[0] == "message":
                msg = "`" + array[1] + ": " + array[3]
                ui.comm.message.emit(msg)


            else:
                pass


# Class that handles uploading of file, creates socket and opens file and uploads file.
class ul_socket:
    def __init__(self, filename, start, ip, port):
        self.setup_ul_socket(ip, port)
        self.setup_ul_file(filename)
        self.upload(start)
        ui.ul_class = self

    def setup_ul_socket(self, ip, port):
        global ui
        global uploading

        ADDR = (ip, port)

        original_socket = socket(AF_INET, SOCK_STREAM)
        original_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sslContext.set_ciphers(
            "NULL-SHA256 AES128-SHA256 AES256-SHA256 AES128-GCM-SHA256 AES256-GCM-SHA384 DH-RSA-AES128-SHA256 DH-RSA-AES256-SHA256 DH-RSA-AES128-GCM-SHA256 DH-RSA-AES256-GCM-SHA384 DH-DSS-AES128-SHA256 DH-DSS-AES256-SHA256 DH-DSS-AES128-GCM-SHA256 DH-DSS-AES256-GCM-SHA384 DHE-RSA-AES128-SHA256 DHE-RSA-AES256-SHA256 DHE-RSA-AES128-GCM-SHA256 DHE-RSA-AES256-GCM-SHA384 DHE-DSS-AES128-SHA256 DHE-DSS-AES256-SHA256 DHE-DSS-AES128-GCM-SHA256 DHE-DSS-AES256-GCM-SHA384 ECDHE-RSA-AES128-SHA256 ECDHE-RSA-AES256-SHA384 ECDHE-RSA-AES128-GCM-SHA256 ECDHE-RSA-AES256-GCM-SHA384 ECDHE-ECDSA-AES128-SHA256 ECDHE-ECDSA-AES256-SHA384 ECDHE-ECDSA-AES128-GCM-SHA256 ECDHE-ECDSA-AES256-GCM-SHA384 ADH-AES128-SHA256 ADH-AES256-SHA256 ADH-AES128-GCM-SHA256 ADH-AES256-GCM-SHA384 AES128-CCM AES256-CCM DHE-RSA-AES128-CCM DHE-RSA-AES256-CCM AES128-CCM8 AES256-CCM8 DHE-RSA-AES128-CCM8 DHE-RSA-AES256-CCM8 ECDHE-ECDSA-AES128-CCM ECDHE-ECDSA-AES256-CCM ECDHE-ECDSA-AES128-CCM8 ECDHE-ECDSA-AES256-CCM8")
        sslContext.load_dh_params("dhparam.pem")
        self.upload_socket = sslContext.wrap_socket(original_socket, server_side=False, )
        self.upload_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        time.sleep(0.5)
        self.upload_socket.connect(ADDR)

    def setup_ul_file(self, filename):
        self.file_size = os.path.getsize(filename)
        send = []
        send.append(filename)
        send.append(self.file_size)
        send = pickle.dumps(send).ljust(1024)
        self.upload_socket.send(send)
        self.buffer_size = 1024
        self.amount_sent = 0
        self.file = open(filename, 'rb')

    def upload(self, start):
        global uploading
        global uploading2
        self.file.seek(0, 0)
        if start != 0:
            self.amount_sent = start
            self.file.seek(start)


        start =  time.time()
        data = self.file.read(self.buffer_size)

        while uploading and self.amount_sent < self.file_size:
            # progress = round((self.amount_sent / self.file_size) * 100)
            # ui.set_value.message.emit(progress)
            self.upload_socket.send(data)
            size = len(data)
            self.amount_sent += (size)
            data = self.file.read(self.buffer_size)
            while uploading2:
                pass

        uploading = False
        uploading2 = False

        end = time.time()
        print("ULTIME ", end-start)
        if self.amount_sent == self.file_size:
            ui.set_value.message.emit(0)
            ui.comm.message.emit("Your upload has completed")


# Class that handles downloading of file, creates socket and opens file and downloads and writes file.
class dl_socket_class:
    def __init__(self, port):
        global ui

        self.setup_socket(port)
        self.setup_file()
        self.download()
        ui.dl_class = self

    def setup_socket(self, port):
        global ui

        tcpSocket = socket(AF_INET, SOCK_STREAM)
        tcpSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        tcpSocket.bind((ui.ip, port))
        tcpSocket.listen(1)

        newsocket, fromaddr = tcpSocket.accept()
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        sslContext.set_ciphers(
            "NULL-SHA256 AES128-SHA256 AES256-SHA256 AES128-GCM-SHA256 AES256-GCM-SHA384 DH-RSA-AES128-SHA256 DH-RSA-AES256-SHA256 DH-RSA-AES128-GCM-SHA256 DH-RSA-AES256-GCM-SHA384 DH-DSS-AES128-SHA256 DH-DSS-AES256-SHA256 DH-DSS-AES128-GCM-SHA256 DH-DSS-AES256-GCM-SHA384 DHE-RSA-AES128-SHA256 DHE-RSA-AES256-SHA256 DHE-RSA-AES128-GCM-SHA256 DHE-RSA-AES256-GCM-SHA384 DHE-DSS-AES128-SHA256 DHE-DSS-AES256-SHA256 DHE-DSS-AES128-GCM-SHA256 DHE-DSS-AES256-GCM-SHA384 ECDHE-RSA-AES128-SHA256 ECDHE-RSA-AES256-SHA384 ECDHE-RSA-AES128-GCM-SHA256 ECDHE-RSA-AES256-GCM-SHA384 ECDHE-ECDSA-AES128-SHA256 ECDHE-ECDSA-AES256-SHA384 ECDHE-ECDSA-AES128-GCM-SHA256 ECDHE-ECDSA-AES256-GCM-SHA384 ADH-AES128-SHA256 ADH-AES256-SHA256 ADH-AES128-GCM-SHA256 ADH-AES256-GCM-SHA384 AES128-CCM AES256-CCM DHE-RSA-AES128-CCM DHE-RSA-AES256-CCM AES128-CCM8 AES256-CCM8 DHE-RSA-AES128-CCM8 DHE-RSA-AES256-CCM8 ECDHE-ECDSA-AES128-CCM ECDHE-ECDSA-AES256-CCM ECDHE-ECDSA-AES128-CCM8 ECDHE-ECDSA-AES256-CCM8")
        sslContext.load_dh_params("dhparam.pem")
        self.sslSocket = sslContext.wrap_socket(newsocket, server_side=True, )
        self.sslSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def setup_file(self):
        data = pickle.loads(self.sslSocket.recv(1024))
        self.filename = data[0]
        self.filesize = data[1]
        self.amount_recv = 0
        self.size = 0

        self.splice = self.filename.split("/")
        self.path = "Downloads/" + self.splice[1]

        try:
            self.size = os.path.getsize(self.path)
        except:
            pass

        try:
            if self.size == self.filesize:
                os.remove(self.path)
                self.size = 0
        except:
            pass

        self.f = open(self.path, 'ab')

    def download(self):
        try:
            self.amount_recv = self.size
        except:
            pass

        start = time.time()
        while ui.dl_running == True and self.amount_recv < self.filesize:
            # progress = round((self.amount_recv / self.filesize) * 100)
            # ui.set_value_dl.message.emit(progress)

            data = self.sslSocket.recv(1024)
            self.amount_recv += len(data)
            self.f.write(data)

        self.f.close()
        end =  time.time()

        print("DLTIME = ", (end-start))
        self.sslSocket.close()

        if (self.amount_recv == self.filesize):
            ui.d_button.message.emit("True")
            ui.set_value_dl.message.emit(0)
            ui.comm.message.emit("Your download has completed")


if __name__ == '__main__':
    global Frame
    global app

    import sys

    app = QtWidgets.QApplication(sys.argv)
    Frame = QtWidgets.QFrame()

    ex = Input()
    ex.show()

    sys.exit(app.exec_())
