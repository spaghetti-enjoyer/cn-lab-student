import socket
import threading
import argparse
import os

# to run from terminal: 
# python3 client.py --address "212.132.114.68" --port 5378

sock = None
username = None
attempted_name = None

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5378

def connect_to_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_port = (host, port)
    sock.connect(host_port)
    print('connected', sock)
    return sock


def receive_from_socket():
    response = ""
    while "\n" not in response:
        response += sock.recv(1).decode("utf-8")

    # print("incoming message: ", response)

    return response


def send_over_socket(data):
    string_bytes = data.encode("utf-8")
    bytes_len = len(string_bytes)
    num_bytes_to_send = bytes_len

    # print("to be sent:", data)

    while num_bytes_to_send > 0:
        num_bytes_to_send -= sock.send(string_bytes[bytes_len-num_bytes_to_send:])


def send_message(message):
    global attempted_name

    # print("received from user:", message)

    if message == "!quit":
        print("exiting...")
        sock.close()
        os._exit(0) # no error code returned

    elif message == "!who":
        send_over_socket("LIST\n")
    
    elif username == None:
        # send the username to the server and see what it spits out
        attempted_name = message
        print(f"attempting login as {attempted_name}")
        send_over_socket(f"HELLO-FROM {attempted_name}\n")

    elif message[0] == "@" and " " in message:
        # splitting and sending valid message to different user
        recipient, content = message.split(" ", 1)
        recipient = recipient[1:] # cut off @
        send_over_socket(f"SEND {recipient} {content}\n")

    # invalid messages
    else: 
        send_over_socket(message)


def receive_incoming_messages():
    global username, sock
    # global attempted_name
    while True:
        message = receive_from_socket()

        if "BUSY" in message:
            print(f"Cannot log in. The server is full!")
            print("exiting...")
            os._exit(0)
        
        elif "LIST-OK" in message:
            message = message[8:-1] # cut off the prefix and suffix
            names = message.split(",")
            print(f"There are {len(names)} online:")
            for name in names:
                print(f"- {name}")

        elif username == None and "BAD-RQST-BODY" in message:
            print(f"Cannot log in as {attempted_name}. That username contains disallowed characters.")
            # reconnect
            sock.close()
            sock = connect_to_server(SERVER_HOST, SERVER_PORT)

        elif "IN-USE" in message:
            print(f"Cannot log in as {attempted_name}. That username is already in use.")
            # reconnect
            sock.close()
            sock = connect_to_server(SERVER_HOST, SERVER_PORT)

        elif "HELLO" in message: # source of exploits af
            username = attempted_name
            print(f"Successfully logged in as {username}!")

        elif "SEND-OK" in message:
            print("The message was sent succesfully")

        elif "BAD-DEST-USER" in message:
            print("The destination user does not exist")

        elif "DELIVERY" in message:
            tag, username, content = message.split(" ", 2)
            print(f"From {username}: {content}")

        elif "BAD-RQST-HDR" in message:
            print("Error: Unknown issue in previous message header.")

        elif "BAD-RQST-BODY" in message:
            print("Error: Unknown issue in previous message body.")

        else:
            print("idk what just happened.")
            # os._exit(0)


if __name__ == "__main__":
    # deal with commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str)
    parser.add_argument("--port", type=int)
    args = parser.parse_args()

    SERVER_HOST = args.address
    SERVER_PORT = args.port

    sock = connect_to_server(SERVER_HOST, SERVER_PORT)

    print("Welcome to Chat Client. Enter your login: test")

    # thread for incoming messages in the background
    receiving = threading.Thread(target = receive_incoming_messages, daemon=True).start()

    while True:
        message = input()
        send_message(message)
    