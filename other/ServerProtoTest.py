import time
import TransportMessage_pb2
import WeChatOnlineNoticeMessage_pb2
import ContactsInfoNoticeMessage_pb2
import FriendTalkNoticeMessage_pb2
from queue import Queue
import threading
import socketserver

allFriendList = list()  # 不包含重复的好友信息
List_Lock = threading.Lock()  # 线程锁
queue = Queue()  # 创建队列


class Myserver(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request
        Thread_recv(conn)


def Thread_send(socket_Server, queue, WeChatId):
    global allFriendList
    try:
        while True:
            msg = queue.get()
            print('Thread_send', msg['FriendId'], WeChatId)
            if msg['FriendId'] == WeChatId:
                SendMessage = TransportMessage_pb2.TransportMessage()
                FriendTalkMessage = FriendTalkNoticeMessage_pb2.FriendTalkNoticeMessage()
                FriendTalkMessage.Content = msg['Content']
                FriendTalkMessage.WeChatId = WeChatId

                SendMessage.MsgType = 1025
                SendMessage.Id = 0
                SendMessage.AccessToken = "ac897dss"
                SendMessage.Content.Pack(FriendTalkMessage)
                byte_data = SendMessage.SerializeToString()
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                socket_Server.send(byte_head)
                socket_Server.send(byte_data)
            else:
                for friend in allFriendList:
                    if friend['WeChatId'] == msg['FriendId']:
                        queue.put(msg)
                        time.sleep(0.000001)  # 只要有个延时就行，不然会导致代码死循环
    except Exception as ex:
        print('Thread_send 异常...', ex)


def Thread_recv(socket_Server):
    try:
        global allFriendList

        global queue

        online = WeChatOnlineNoticeMessage_pb2.WeChatOnlineNoticeMessage()
        while True:
            Head_data = socket_Server.recv(4)  # 接收数据头 4个字节,
            data_len = int.from_bytes(Head_data, byteorder='big')
            print('data_len=', data_len)
            protobufdata = socket_Server.recv(data_len)

            tmessage = TransportMessage_pb2.TransportMessage()
            tmessage.ParseFromString(protobufdata)

            i_id = tmessage.Id
            i_msgtype = tmessage.MsgType
            now_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(now_time, ' id:', i_id, 'msgType:', i_msgtype)
            if i_msgtype == 0:
                print('异常')
                for friend in allFriendList:
                    if friend['WeChatId'] == online.WeChatId:
                        print('下线WeChatId：', online.WeChatId)
                        if List_Lock.acquire():
                            allFriendList.remove(friend)
                            List_Lock.release()
                            break
                socket_Server.close()
                break
            if i_msgtype == 1010:
                print(now_time, ' 服务器接收到心跳包...好友在线个数：', len(allFriendList))
                # print(now_time,' 服务器接收到心跳包...')
            if i_msgtype == 1020:
                print(now_time, ' 服务器接收到上线通知...')
                # 有上线通知，将好友信息和socket_Server套接字存放在buf中，
                # 这样可以将好友A的信息转发给好友B，做成及时聊天工具
                # 有下线通知，将好友信息和socket_Server套接字从buf中去掉
                # 服务器端功能就是收集上线和下线通知，转发聊天消息

                tmessage.Content.Unpack(online)

                print(now_time, ' WeChatNo:' + online.WeChatNo, 'WeChatId:' + online.WeChatId,
                      'WeChatNick:' + online.WeChatNick)

                # 没有添加就添加，列表中有的话就更新
                f_dict = {"WeChatId": online.WeChatId, "socket_Server": socket_Server,
                          "WeChatOnlineNoticeMessage": online}
                isAddFriend = True
                for friend in allFriendList:
                    if friend['WeChatId'] == online.WeChatId:
                        isAddFriend = False
                        print('已上线WeChatId：', online.WeChatId)

                if isAddFriend:
                    if List_Lock.acquire():
                        allFriendList.append(f_dict)
                        List_Lock.release()
                        # 新建转发好友消息的线程
                        t_send = threading.Thread(target=Thread_send, args=(socket_Server, queue, online.WeChatId))
                        t_send.start()

            if i_msgtype == 1021:
                print(now_time, '服务器接收到下线通知')
                for friend in allFriendList:
                    if friend['WeChatId'] == online.WeChatId:
                        print('下线WeChatId：', online.WeChatId)
                        if List_Lock.acquire():
                            allFriendList.remove(friend)
                            List_Lock.release()
                            break
                socket_Server.close()
                break  # 退出while
            if i_msgtype == 1022:
                print(now_time, '服务器接收到客户端请求在线好友信息通知')
                contacts = ContactsInfoNoticeMessage_pb2.ContactsInfoNoticeMessage()
                for friend in allFriendList:
                    friendmessage = contacts.Friends.add()
                    friendmessage.FriendId = friend['WeChatId']
                    # contacts.add(friendmessage)
                transportMessage = TransportMessage_pb2.TransportMessage()  # 注意括号不要掉了，
                transportMessage.MsgType = 1023
                transportMessage.Id = 0
                transportMessage.AccessToken = "ac897dss"
                transportMessage.Content.Pack(contacts)

                byte_data = transportMessage.SerializeToString()
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                socket_Server.send(byte_head)
                socket_Server.send(byte_data)
            if i_msgtype == 1024:
                print(now_time, '转发好友聊天内容')
                FriendTalkMessage = FriendTalkNoticeMessage_pb2.FriendTalkNoticeMessage()
                tmessage.Content.Unpack(FriendTalkMessage)
                print(now_time, online.WeChatId, FriendTalkMessage.FriendId, str(FriendTalkMessage.Content, 'utf-8'))
                # if FriendTalkMessage.FriendId == online.WeChatId:

                msg = {'FriendId': FriendTalkMessage.FriendId, 'Content': FriendTalkMessage.Content}

                queue.put(msg)

                """SendMessage = TransportMessage_pb2.TransportMessage()#注意括号不要掉了，
                SendMessage.MsgType = 1025
                SendMessage.Id = 0
                SendMessage.AccessToken ="ac897dss"
                SendMessage.Content.Pack(FriendTalkMessage)
                byte_data = SendMessage.SerializeToString()
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                socket_Server.send(byte_head)
                socket_Server.send(byte_data)"""


    except Exception as ex:
        print('Thread_recv 异常...', ex)
        for friend in allFriendList:
            if friend['WeChatId'] == online.WeChatId:
                print('下线WeChatId：', online.WeChatId)
                if List_Lock.acquire():
                    allFriendList.remove(friend)
                    List_Lock.release()
                    break
    finally:
        socket_Server.close()


if __name__ == "__main__":
    server = socketserver.ThreadingTCPServer(('127.0.0.1', 11087), Myserver)
    server.serve_forever()
