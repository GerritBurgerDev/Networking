#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
import pickle
import json
from threading import Thread
users = {}
running = True
ADDR = None
SERVER = None


def accept_incoming_connections(client, client_address):
    """Sets up handling for incoming clients."""
    if running is False:
        return
    print("%s:%s has connected.\n" % client_address)
    client.send(bytes("Connected! Please Enter your name", "utf8"))

    addresses[client] = client_address

    name = client.recv(BUFSIZ)
    rec_array = pickle.loads(name)

    name  = rec_array[0]

    while name in users:
        array = ["Nickname already in use, please try again!"]
        array = pickle.dumps(array)
        array = array.ljust(1024)
        client.send(array)
        r_array = pickle.loads(client.recv(BUFSIZ))
        name = r_array[0]

    array = [1]
    array = pickle.dumps(array)
    array = array.ljust(1024)
    client.send(array)

    print("%s has joined the chat.\n" % name)

    array = ["`Welcome %s!" % name]
    array = pickle.dumps(array)
    array = array.ljust(1024)
    client.send(array)
    handle_client(client,name)

def handle_client(client, name):
    """Handles a single client connection."""

    global users
    global running
    users[name] = [addresses[client], True]

    msg = "`%s has joined the chat!" % name
    array = [msg]
    broadcast(array)
    clients[client] = name
    broadcast(users)

    while True:
        msg = client.recv(BUFSIZ)
        if msg == b'':
            break

        else:
            rec_array = pickle.loads(msg)

            if rec_array[0] == 0:

                if rec_array[1] == "{quit}":
                    print("%s has left the chat.\n" % name)
                    client.close()

                    del clients[client]
                    del users[name]
                    if len(users) != 0:
                        if running is True:
                            broadcast(users)
                            msg = "~%s has left the chat." % name
                            array = [msg]
                            broadcast(array)
                    break

            elif rec_array[0] == 1:
                array = [rec_array[1],rec_array[2]]
                broadcast(array)

            elif rec_array[0] == 69:
                whisp = whisper(rec_array)

            elif rec_array[0] == 100:
                global ADDR

                running = False
                print("Server closed.\n")
                array = ["~Server disconnected"]
                del users[name]
                broadcast(users)
                broadcast(array)
                dummy = socket(AF_INET,SOCK_STREAM)
                dummy.connect(ADDR)

                break


def users_broadcast(users):
    """Users list."""

    for sock in clients:
        sock.send(users)

def broadcast(array):
    """Broadcasts a message to all the clients."""

    array = pickle.dumps(array)
    array = array.ljust(1024)

    for sock in clients:
        sock.send(array)

def whisper(array):
    """Wisper a message to a certain user """

    fr = array[1]
    to = array[2]
    message = array[3]

    if to not in users:
        for client in clients:
            if clients[client] == fr:
                client.send(bytes("Whisper failed","utf8"))
                return

    for client in clients:
        if clients[client] == to:
            dest = client

    send_array = [69,fr,to,message]
    dest.send(pickle.dumps(send_array).ljust(1024))


clients = {}
addresses = {}

BUFSIZ = 1024

def setHost(ip, port):
    """Set the ip and port for the server and client to connect to"""

    HOST = ip
    PORT = port

    return HOST, PORT

def run(ip, port):
    """Start the server"""
    global SERVER
    global ADDR

    HOST, PORT = setHost(ip, port)
    ADDR = (HOST, PORT)

    SERVER = socket(AF_INET, SOCK_STREAM)
    SERVER.bind(ADDR)

    SERVER.listen(5)
    print("Waiting for connection...\n")

    while running is True:
        client, client_address = SERVER.accept()

        if running is False:

            break

        ACCEPT_THREAD = Thread(target=accept_incoming_connections, args=(client, client_address))
        ACCEPT_THREAD.start()
