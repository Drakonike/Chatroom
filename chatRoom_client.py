# -*- coding: utf-8 -*-
"""
Created on Mon May 13 2024
Elaborato traccia 1 - Programmazione di reti 
@author: giovanni.tentelli@studio.unibo.it
0000921144 Giovanni Tentelli
"""
import socket
from threading import Thread, Lock, Event
import sys
import time
import atexit
import tkinter as tkt

BUFSIZ = 1024
RECONNECT_ATTEMPTS = 5
EXIT = Event()
RESTART_CONNECTION = Event()
QUIT = "!quit"


def connect(address):
    attemps = 0
    while attemps < RECONNECT_ATTEMPTS:
        try:
            attemps = attemps + 1
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(address)
            s.settimeout(10)
            return s
        except socket.error as e:
            print("socket error: {}, reconnecting".format(e))
            print('attempt n.', attemps)
            time.sleep(5)
    print('connection attemps failed, shutting down')
    sys.exit()


def connectionMantainer(client, lock, EXIT, RESTART_CONNECTION):
    while True:
        time.sleep(10)
        if EXIT.is_set() or RESTART_CONNECTION.is_set():
            break
        try:
            client.send(bytes('', "utf8"))
            client.recv(BUFSIZ)
        except socket.error as e:
            print("{}".format(e))
            lock.acquire()
            RESTART_CONNECTION.set()
            lock.release()
            break


def receiver(client, chatLog, gui, lock, EXIT, RESTART_CONNECTION):
    while True:
        if EXIT.is_set() or RESTART_CONNECTION.is_set():
            break
        try:
            msg = client.recv(BUFSIZ).decode("utf8")
            if len(msg) == 0:
                lock.acquire()
                EXIT.set()
                gui.quit()
                lock.release()
                break
            else:
                chatLog.insert(tkt.END, msg)
        except socket.error as e:
            print("{}".format(e))
            lock.acquire()
            RESTART_CONNECTION.set()
            gui.quit()
            lock.release()
            break
        except Exception as e:
            print("{}".format(e))
            lock.acquire()
            EXIT.set()
            gui.quit()
            lock.release()
            break


def sender(client, messages, gui, lock, EXIT, RESTART_CONNECTION):
    try:
        msg = messages.get().strip()
        messages.set("")
        if len(msg) > 0 and msg != QUIT:  # user SHOULD NOT be able to send empty strings
            try:
                client.send(bytes(msg, "utf8"))
            except socket.error as e:
                print('Could not send message!')
                print("{}".format(e))
                lock.acquire()
                RESTART_CONNECTION.set()
                gui.quit()
                lock.release()

    except Exception as e:
        print("{}".format(e))
        lock.acquire()
        EXIT.set()
        gui.quit()
        lock.release()


def on_closing(client, messages, gui, lock, EXIT, RESTART_CONNECTION):
    messages.set(QUIT)
    sender(client, messages, gui, lock, EXIT, RESTART_CONNECTION)
    gui.quit()
    print('Quitting application!')
    lock.acquire()
    EXIT.set()
    gui.quit()
    gui.destroy()
    lock.release()


def createGui(client, lock, EXIT, RESTART_CONNECTION):
    gui = tkt.Tk()
    gui.title("Elaborato traccia 1")
    messages_frame = tkt.Frame(gui)
    messages = tkt.StringVar()
    #messages.set("Write here.")
    scrollbar = tkt.Scrollbar(messages_frame)
    chat_log = tkt.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tkt.RIGHT, fill=tkt.Y)
    chat_log.pack(side=tkt.LEFT, fill=tkt.BOTH)
    chat_log.pack()
    messages_frame.pack()
    entry_field = tkt.Entry(gui, textvariable=messages)
    entry_field.bind("<Return>", lambda: sender(client, messages, gui, lock, EXIT, RESTART_CONNECTION))
    entry_field.pack()
    send_button = tkt.Button(gui, text="Send",
                             command=lambda: sender(client, messages, gui, lock, EXIT, RESTART_CONNECTION))
    send_button.pack()
    gui.protocol("WM_DELETE_WINDOW", lambda: on_closing(client, messages, gui, lock, EXIT, RESTART_CONNECTION))
    return chat_log, gui


def main(argv):
    HOST = input('Insert host server:')

    try:
        socket.inet_aton(HOST)
    except socket.error as e:
        print("{}".format(e))
        print('exiting application')
        sys.exit(1)

    PORT = input('Insert host server port:')

    if not PORT:
        PORT = 50000
    else:
        PORT = int(PORT)

    ADDR = (HOST, PORT)

    def close_socket():
        client.close()

    atexit.register(close_socket)

    lock = Lock()
    gui = None
    while True:
        client = connect(ADDR)
        print('Connection succesful!\n')
        client.settimeout(None)

        if gui is None:
            chat_log, gui = createGui(client, lock, EXIT, RESTART_CONNECTION)

        Thread(target=connectionMantainer, args=(client, lock, EXIT, RESTART_CONNECTION)).start()
        receive_thread = Thread(target=receiver, args=(client, chat_log, gui, lock, EXIT, RESTART_CONNECTION))
        receive_thread.start()

        tkt.mainloop()
        while True:
            time.sleep(5)
            lock.acquire()
            if EXIT.is_set():
                close_socket()
                lock.release()
                print('Application closed!')
                sys.exit(0)
            elif RESTART_CONNECTION.is_set():
                print('no message, reattemping connection!')
                close_socket()
                RESTART_CONNECTION.clear()
                break
            lock.release()


if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        EXIT.is_set()
        sys.exit(1)
