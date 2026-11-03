# -*- coding: utf-8 -*-
"""
Created on Mon May 13 2024
Elaborato traccia 1 - Programmazione di reti 
@author: giovanni.tentelli@studio.unibo.it
0000921144 Giovanni Tentelli
"""
import socket
from  threading import Thread, Lock, Event
import sys
import time
import atexit

BUFSIZ = 1024
RECONNECT_ATTEMPTS = 5
EXIT = Event()
RESTART_CONNECTION = Event()

def connectionMantainer(client, lock, EXIT, RESTART_CONNECTION):
    while True:
        if EXIT.is_set() or RESTART_CONNECTION.is_set():
            return None
        time.sleep(10)
        try:
            client.send(bytes('Cooola', "utf8"))
            client.recv(BUFSIZ)
        except socket.error as e:
            print("connection mantainer error: {}".format(e))
            lock.acquire()
            RESTART_CONNECTION.set()
            lock.release()
            return None

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
            print('attempt n.',attemps)
            time.sleep(5)
    print('connection attemps failed, shutting down')
    sys.exit()

def reciveMessages(client, lock, EXIT, RESTART_CONNECTION):
    while True:
        if EXIT.is_set() or RESTART_CONNECTION.is_set():
            return None
        try:
            msg = client.recv(BUFSIZ).decode("utf8")
            if len(msg) == 0:
                lock.acquire()
                EXIT.set()
                lock.release()
                return None
            else:
                print(msg)
        except socket.error as e:
            print("receptor error: {}".format(e))
            lock.acquire()
            RESTART_CONNECTION.set()
            lock.release()
            return None
     
def sendMessage(client, lock, EXIT, RESTART_CONNECTION):
    while True:
        if EXIT.is_set() or RESTART_CONNECTION.is_set():
            return None
        msg = input().strip()
        if len(msg) > 0: #user SHOULD NOT be able to send empty strings
            try:
                client.send(bytes(msg, "utf8"))
            except socket.error as e:
                print('Could not send message!')
                print("{}".format(e))
                lock.acquire()
                RESTART_CONNECTION.set()
                if msg == '!quit': 
                    EXIT.set()
                lock.release()
                return None
        if msg == '!quit':
            print('Quitting application!')
            lock.acquire()
            EXIT.set()
            lock.release()
            return None
        msg = ''

def main(argv):
    HOST = input('Inserire il Server host: ')
    
    try:
        socket.inet_aton(HOST) #check if address is valid
    except socket.error as e:
         print("{}".format(e))
         print('exiting application')
         sys.exit(1)
         
    PORT = input('Inserire la porta del server host: ')
         
    if not PORT:
        PORT = 50000
    else:
        PORT = int(PORT)
        
    ADDR = (HOST, PORT)
    
    def close_socket():
        client.close()
    atexit.register(close_socket)
    
    lock = Lock()
    
    while True:
        client = connect(ADDR)
        client.settimeout(None)
        print('Connection succesful!\n')
        if(client != None):
            #mantainer_thread = Thread(target = connectionMantainer, args = (client, lock, EXIT, RESTART_CONNECTION))
            #mantainer_thread.start()
            receiver_thread = Thread(target = reciveMessages, args = (client, lock, EXIT, RESTART_CONNECTION))
            receiver_thread.start()
            sender_thread = Thread(target = sendMessage, args = (client, lock, EXIT, RESTART_CONNECTION))
            sender_thread.start()
            
            while True:
                time.sleep(5)
                if EXIT.is_set():
                    close_socket()
                    print('Application closed!')
                    sys.exit(0)
                elif RESTART_CONNECTION.is_set():
                    print('no message, reattemping connection!')
                    close_socket()
                    #mantainer_thread.join()
                    receiver_thread.join()
                    sender_thread.join()
                    lock.acquire()
                    RESTART_CONNECTION.clear()
                    lock.release()
                    print('bongo')
                    break
        
if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        EXIT.is_set()
        sys.exit(1)
