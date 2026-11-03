# -*- coding: utf-8 -*-
"""
Created on Mon May 13 2024
Elaborato traccia 1 - Programmazione di reti 
@author: giovanni.tentelli@studio.unibo.it
0000921144 Giovanni Tentelli
"""
import socket
from threading import Thread, Lock
import sys
import atexit


def add_client(client, cl_address):
    CLIENTS[client] = cl_address


def remove_client(client):
    if client in CLIENTS.keys():
        del CLIENTS[client]
    if client in USERNAMES.keys():
        del USERNAMES[client]


def add_username(client, username):
    USERNAMES[client] = username


def connection_restarter(server, lock):
    while not EXITING:
        accepter_thread = Thread(target=connection_accepter, args=(server, lock))
        accepter_thread.start()
        accepter_thread.join()


def connection_accepter(server, lock):
    print('Waiting for clients...')
    client = None
    while True:
        try:
            client, cl_address = server.accept()
            client.settimeout(None)
            if client is not None:
                print("%s:%s is now connected." % cl_address)
                lock.acquire()
                add_client(client, cl_address)
                lock.release()
                Thread(target=clientManager, args=(client, lock)).start()
        except socket.error as e:
            print("socket error:{}".format(e))
            if client is not None:
                lock.acquire()
                remove_client(client)
                lock.release()
            return None


def clientManager(client, lock):
    try:
        username = None
        client.send(
            bytes("[SERVER]: Hi! Digit here your name (must be at least three caracthers long), then press enter!",
                  "utf8"))
        username = client.recv(BUFSIZ).decode("utf8").strip()

        while len(username) < 3 or username == '!quit' or username in USERNAMES.values():
            client.send(
                bytes("[SERVER]: Name is already taken or smaller than 3 caracthers, please digit another name.",
                      "utf8"))
            username = client.recv(BUFSIZ).decode("utf8").strip()

        lock.acquire()
        add_username(client, username)
        print('user %s:%s ' % CLIENTS.get(client), 'has choosen username %s' % username)
        lock.release()

        benvenuto = '[SERVER]: Welcome %s! To leave chat write {!quit}.' % username
        client.send(bytes(benvenuto, "utf8"))
        data = "%s joined the chat!" % username

        lock.acquire()
        send_all_clients(bytes(data, "utf8"), '[SERVER]')
        lock.release()

        while True:
            data = client.recv(BUFSIZ).decode("utf8")
            if data == '!quit':
                lock.acquire()
                print('Client %s:%s,' % CLIENTS.get(client),
                      'with username %s is being removed from userlist. Reason: Quitted\n' % USERNAMES.get(client))
                remove_client(client)
                send_all_clients(bytes('%s has quitted.' % username, 'utf8'), '[SERVER]')
                lock.release()
                client.close()
                return None
            elif len(data) > 0:
                print(username, '>', data)
                lock.acquire()
                send_all_clients(bytes(data, "utf8"), username)
                lock.release()

    except socket.error as e:
        # if any case of socket error always remove client from userlist and terminate thread
        lock.acquire()
        print("User %s:%s has recurred a error: {}\n".format(e) % CLIENTS.get(client))
        if client in USERNAMES.keys():
            print('Client %s:%s,' % CLIENTS.get(client),
                  'with username %s is being removed from userlist. Reason: Disconnected\n' % USERNAMES.get(client))
            send_all_clients(bytes('%s has disconnected.' % USERNAMES.get(client), 'utf8'), '[SERVER]')
        else:
            print('Client %s:%s,' % CLIENTS.get(client), 'is being removed from userlist. Reason: Disconnected\n')
        remove_client(client)
        lock.release()
        return None
    except Exception as e:
        print("A Client error as occurred: {}\n".format(e))
        client.close()
        return None


def send_all_clients(message, sender_name):
    for client in CLIENTS:
        if USERNAMES.get(client) != sender_name:
            try:
                client.send(bytes(sender_name + ': ', 'utf8') + message)
            except socket.error as e:
                print("{}".format(e))


def main(argv):
    global CLIENTS
    global USERNAMES
    global BUFSIZ
    global EXITING

    CLIENTS = dict()
    USERNAMES = dict()
    BUFSIZ = 1024
    EXITING = False

    HOST = ''
    PORT = 51000

    def close_socket():
        lock.acquire()
        send_all_clients(bytes('server is shutting down', 'utf8'), '[SERVER]')
        lock.release()
        server.close()

    atexit.register(close_socket)

    lock = Lock()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.settimeout(None)
    try:
        server.bind((HOST, PORT))
        server.listen()
    except socket.error as e:
        print('during server initializzation a error has occurred :')
        print("{}".format(e))
        server.close()
        sys.exit(1)

    Thread(target=connection_restarter, args=(server, lock)).start()
    print('Server started!\n')

    while True:
        if input() == 'quit':
            if input('Are you sure? y/n: ') == 'y':
                EXITING = True
                close_socket()
                print('Server closed!\n')
                sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
