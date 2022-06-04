import socket
import threading


def thread_recv(tcpCliSock):
    # 接受线程
    while True:
        response = tcpCliSock.recv(1024)
        print(response.decode('utf-8'))


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    t_rev = threading.Thread(target=thread_recv, args=(sock,))
    t_rev.start()
    try:
        while True:
            message = input()
            sock.sendall(bytes(message, 'utf-8'))
    finally:
        sock.close()
