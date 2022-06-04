from socket import *
import TransportMessage_pb2
import WeChatOnlineNoticeMessage_pb2
import ContactsInfoNoticeMessage_pb2
import FriendTalkNoticeMessage_pb2
import threading
import time

Id = 0
IsConnect = False
onlineNotice_bytes = None
WeChatId = None
contacts = None


def HearBeatReq_bytes():
    global Id
    Id += 1
    transportMessage = TransportMessage_pb2.TransportMessage()  # 注意括号不要掉了，
    transportMessage.MsgType = 1010
    transportMessage.Id = Id
    transportMessage.AccessToken = "ac897dss"
    # print('心跳包数据...Id=',Id)
    return transportMessage.SerializeToString()


def OfflineNotice_bytes():
    global Id
    Id += 1
    transportMessage = TransportMessage_pb2.TransportMessage()  # 注意括号不要掉了，
    transportMessage.MsgType = 1021
    transportMessage.Id = Id
    transportMessage.AccessToken = "ac897dss"
    print('下线通知...Id=', Id)
    return transportMessage.SerializeToString()


def OnlineNotice_bytes():
    global Id
    global WeChatId
    time_t = int(time.time())

    WeChatId = "id_" + str(time_t)  # 随机生成一个WeChatId
    print(WeChatId)
    Id += 1
    transportMessage = TransportMessage_pb2.TransportMessage()  # 注意括号不要掉了，
    transportMessage.MsgType = 1020
    transportMessage.Id = Id
    transportMessage.AccessToken = "ac897dss"

    weChatOnlineNotice = WeChatOnlineNoticeMessage_pb2.WeChatOnlineNoticeMessage()
    weChatOnlineNotice.WeChatId = WeChatId
    weChatOnlineNotice.WeChatNo = "qdj_cancle"
    weChatOnlineNotice.WeChatNick = "昵称001"
    weChatOnlineNotice.Gender = 0
    weChatOnlineNotice.Country = "中国"
    print('上线通知...Id=', Id)
    transportMessage.Content.Pack(weChatOnlineNotice)

    return transportMessage.SerializeToString()


def GetOnlineFriendNotice_bytes():
    global Id
    Id += 1
    transportMessage = TransportMessage_pb2.TransportMessage()  # 注意括号不要掉了，
    transportMessage.MsgType = 1022
    transportMessage.Id = Id
    transportMessage.AccessToken = "ac897dss"
    print('获取在线好友通知...Id=', Id)
    return transportMessage.SerializeToString()


def SendChatContentNotice_bytes(FriendId, content):
    global Id
    global WeChatId
    Id += 1
    # print(FriendId,content)
    transportMessage = TransportMessage_pb2.TransportMessage()  # 注意括号不要掉了，
    transportMessage.MsgType = 1024
    transportMessage.Id = Id
    transportMessage.AccessToken = "ac897dss"
    FriendTalkNotice = FriendTalkNoticeMessage_pb2.FriendTalkNoticeMessage()
    FriendTalkNotice.WeChatId = WeChatId  # 随机生成一个WeChatId
    FriendTalkNotice.FriendId = FriendId
    FriendTalkNotice.Content = bytes(content, 'utf-8')
    transportMessage.Content.Pack(FriendTalkNotice)

    print(WeChatId, '给好友', FriendId, '发送消息', content)
    return transportMessage.SerializeToString()


def thread_HearBeat(tcpCliSock):
    global IsConnect
    try:
        t = 1
        print('thread_HearBeat=', IsConnect)
        while IsConnect:
            if t > 10:
                t = 1
                hearBeat_data = HearBeatReq_bytes()
                byte_data = hearBeat_data
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                tcpCliSock.send(byte_head)
                tcpCliSock.send(byte_data)
                # print('10秒定时发送心跳包...\r\n发送数据[0].退出；[1].心跳包；[2].上线通知>')
            time.sleep(1)
            t += 1

    except Exception as ex:
        print('tcpCliSock异常', ex)
    finally:
        tcpCliSock.close()


def thread_recv(tcpCliSock):
    global IsConnect
    global contacts
    try:
        while IsConnect:
            Head_data = tcpCliSock.recv(4)  # 接收数据头 4个字节,
            data_len = int.from_bytes(Head_data, byteorder='big')
            print('data_len=', data_len)
            protobufdata = tcpCliSock.recv(data_len)

            tmessage = TransportMessage_pb2.TransportMessage()
            tmessage.ParseFromString(protobufdata)

            i_id = tmessage.Id
            i_msgtype = tmessage.MsgType
            now_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(now_time, ' id:', i_id, 'msgType:', i_msgtype)
            if i_msgtype == 0:
                print('异常')
                break
            if i_msgtype == 1023:
                print(now_time, ' 接收到在线好友消息：')
                print(tmessage.Content)
                contactsMessage = ContactsInfoNoticeMessage_pb2.ContactsInfoNoticeMessage()
                tmessage.Content.Unpack(contactsMessage)
                contacts = contactsMessage.Friends
                index = 0
                for friend in contacts:
                    index += 1
                    print(index, '在线好友Id：' + friend.FriendId)
            if i_msgtype == 1025:
                print(now_time, '接收到好友消息：')
                FriendTalkMessage = FriendTalkNoticeMessage_pb2.FriendTalkNoticeMessage()
                tmessage.Content.Unpack(FriendTalkMessage)
                print(now_time, FriendTalkMessage.FriendId, '发来消息：' + str(FriendTalkMessage.Content, 'utf-8'))



    except Exception as ex:
        print('thread_recv异常', ex)
    finally:
        tcpCliSock.close()


def main():
    global IsConnect
    global onlineNotice_bytes
    global WeChatId
    HOST = '127.0.0.1'
    PORT = 11087
    BUFSIZ = 1024
    ADDR = (HOST, PORT)

    tcpCliSock = socket(AF_INET, SOCK_STREAM)
    tcpCliSock.connect(ADDR)
    IsConnect = True

    t_hearBeat = threading.Thread(target=thread_HearBeat, args=(tcpCliSock,))
    t_hearBeat.start()  # 启动心跳线程
    t_rev = threading.Thread(target=thread_recv, args=(tcpCliSock,))
    t_rev.start()  # 启动心跳线程
    # friendInfoList = list()
    try:
        while IsConnect:

            data1 = input('[0].下线退出；\n[1].心跳包；\n[2].上线通知；\n[3].获取在线好友信息;\n[4].给所有在线好友发送消息；\n>')
            print('输入指令：', data1)
            if data1 == '0':
                Offline_data = OfflineNotice_bytes()
                byte_data = Offline_data
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                tcpCliSock.send(byte_head)
                tcpCliSock.send(byte_data)
                IsConnect = False
                break
            if data1 == '1':
                hearBeat_data = HearBeatReq_bytes()
                byte_data = hearBeat_data
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                tcpCliSock.send(byte_head)
                tcpCliSock.send(byte_data)
            if data1 == '2':
                if onlineNotice_bytes is None:
                    onlineNotice_bytes = OnlineNotice_bytes()
                byte_data = onlineNotice_bytes
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                tcpCliSock.send(byte_head)
                tcpCliSock.send(byte_data)
            if data1 == '3':
                byte_data = GetOnlineFriendNotice_bytes()
                byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                tcpCliSock.send(byte_head)
                tcpCliSock.send(byte_data)
            if data1 == '4':
                if not contacts is None:
                    for friend in contacts:
                        if not WeChatId == friend.FriendId:
                            byte_data = SendChatContentNotice_bytes(friend.FriendId, 'hello,我是' + WeChatId)
                            byte_head = (len(byte_data)).to_bytes(4, byteorder='big')
                            tcpCliSock.send(byte_head)
                            tcpCliSock.send(byte_data)


    except Exception as identifier:
        print('退出程序！', IsConnect)
    finally:
        tcpCliSock.close()


if __name__ == "__main__":
    main()


