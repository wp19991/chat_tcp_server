import socketserver
import time

members = []


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        global members, message_data
        # 有用户连接服务器，保存用户信息
        print('客户端连接:', self.client_address)
        members.append([self.client_address, self.request])
        self.request.sendall(bytes('欢迎来到聊天室，当前有{}个人在线'.format(len(members)), 'utf-8'))
        try:
            while True:
                data = self.request.recv(1024)
                if not data:
                    break
                # 返回的信息
                res = str(len(members)) + "在线 " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + " " + \
                      "用户" + str(self.client_address) + ":" + data.decode('utf-8')
                print(res)
                # 向当前在线的所有的用户发送消息
                for i in members:
                    if i[0] != self.client_address:
                        i[1].sendall(bytes(res, 'utf-8'))
        finally:
            # 用户失去链接,删去用户的信息
            delete_member_index = 0
            for i, d in enumerate(members):
                if d == self.client_address:
                    delete_member_index = i
            del members[delete_member_index]
            print('客户端离线:', self.client_address)
            self.request.close()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
    ip, port = server.server_address
    print('Server loop running in ip:', str(ip) + ":" + str(port))
    server.serve_forever()
