import socket
import argparse
import select

# https://realpython.com/python-sockets/
# to run from terminal:
# python3 server.py --address "127.0.0.1" --port 5378

CAPACITY = 16
FAILED_TO_SEND = 1

clients = {} # socket -> username

def receive_from_socket(sock):
    # print('hafiahf: ', sock.recv(1).decode("utf-8"))
    response = sock.recv(1).decode("utf-8")

    print("response:", response, '.', sep='|')

    if response == None:
        print(f"Client {sock} has disconnected")
        sock.close()
        del clients[sock]

    if response == "":
        print(f"Client {sock} has disconnecteddd")
        sock.close()
        del clients[sock]

    while "\n" not in response:
        response += sock.recv(1).decode("utf-8")
    return response


def send_over_socket(sock, data):

    print("to be sent:", data)

    string_bytes = data.encode("utf-8")
    bytes_len = len(string_bytes)
    num_bytes_to_send = bytes_len

    while num_bytes_to_send > 0:
        try:
            num_bytes_to_send -= sock.send(string_bytes[bytes_len-num_bytes_to_send:])
        except BrokenPipeError:
            print(f"Client {sock} has disconnected")
            sock.close()
            del clients[sock]
            return FAILED_TO_SEND


def handle_incoming_message(client, message):

    print("length:", len(clients))
    print("connected clients:", clients.values())

    if clients[client] == None:
        if "HELLO-FROM" in message:

            # try to log em in
            if len(clients) > CAPACITY:
                send_over_socket(client, "BUSY\n")
                client.close()
                del clients[client]
                return
            
            header, username = message.split(" ", 1)
            username = username[:-1] # cut off \n

            if " " in username or "," in username or "\\n" in username:
                send_over_socket(client, "BAD-RQST-BODY\n")
            
            elif username in list(clients.values()):
                send_over_socket(client, "IN-USE\n")
            
            elif username not in clients.values():
                send_over_socket(client, f"HELLO {username}\n")
                clients[client] = username
            
        else:
            send_over_socket(client, "BAD-RQST-HDR\n")

    else:
        print('message is: ', message)

        if "HELLO-FROM" in message:
            send_over_socket(client, "BAD-RQST-HDR\n")

        if "LIST" in message:
            res = "LIST-OK "
            for user in clients.values():
                res += user + ","
            res = res[:-1] # truncate the comma at the end
            res += "\n"
            send_over_socket(client, res)

        elif "SEND" in message:
            header, user, body = message.split(" ", 2)

            # print("to:", user)
            # print("all users:", names_list)

            if len(body) < 2:
                send_over_socket(client, "BAD-RQST-BODY\n")
                return

            if user not in clients.values():
                send_over_socket(client, "BAD-DEST-USER\n")
                return
            recipient = list(filter(lambda x: clients[x] == user, clients))[0]
            if send_over_socket(recipient, f"DELIVERY {clients[client]} {body}\n") == FAILED_TO_SEND:
                return
            send_over_socket(client, "SEND-OK\n")

        # I assume this is whats expected cos how else do you differentiate whats body and whats header related
        # elif len(message) < 2: 
        #     send_over_socket(client, "BAD-RQST-HDR\n")

        else:
            send_over_socket(client, "BAD-RQST-BODY\n")


if __name__ == "__main__":

    # deal with commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str)
    parser.add_argument("--port", type=int)
    args = parser.parse_args()

    server_host = args.address
    server_port = args.port

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((server_host, server_port))
    server_socket.listen()

    print("Server is on\n")

    while True: 
        sockets = [server_socket] + list(clients.keys())
        rdlist, wrlist, exlist = select.select(sockets, [], [])
        for socket in rdlist:
            if socket is server_socket:
                connection, address = server_socket.accept()
                clients[connection] = None
                print("new connection!")
            else:    
                message = receive_from_socket(socket)

                print("received:", message, ".", sep="|")

                # message evt handler
                handle_incoming_message(socket, message)
