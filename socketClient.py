# coding=utf-8
import os
import socket
import fcntl
import threading
from socketServer import SentenceUtil

# 客户端流程为：
# 1. 创建接口
# 2. 发起连接
#
# 注意：
# 创建接口参数同socket server相同
# 发起连接的函数为socket.connect(ip,port)
# ip与port为socket server端的ip和监听port。

BUFFERSIZE = 1024

server_ip = '127.0.0.1'
server_port = 12345
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((server_ip, server_port))
print("连接服务器成功，服务器地址与端口为 {} {}".format(server_ip, str(server_port)))


def saveFile(buf, fileName):
    if not os.path.exists(fileName):
        with open(fileName, 'w') as f:
            f.write(buf)
            print('文件不存在，创建并写入文件成功')
    else:
        with open(fileName, 'a') as f:
            SentenceUtil.setSentenceByFile(file_name=fileName)
            sentence = SentenceUtil.getSentence()
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            print('成功获取文件锁')
            buf_to_list = buf.split(sep='\n')
            for item in buf_to_list:
                if (item + '\n') not in sentence:
                    f.write(item + '\n')
                else:
                    print('句子' + item + ' 重复，写入失败')


def sendAndRecv():
    while True:
        try:
            sample_data1 = "sentence:4,5,9#end"
            sample_data2 = "talk:你好吗？#end"
            print("【提醒】请输入要发给服务器的话，样例为 {} 以及 {}".format(sample_data1, sample_data2))
            data = input(">")
            # 发送数据
            byteswritten = 0
            while byteswritten < len(data):
                startpos = byteswritten
                endpos = min(byteswritten + BUFFERSIZE, len(data))
                byteswritten += client.send(data[startpos:endpos].encode())
                print("【提醒】客户端一共发送了 %d bytes 给了服务器" % byteswritten)

            # 接受数据，和发送数据串行
            buf = client.recv(BUFFERSIZE).decode()
            if buf:
                print("【提醒】服务器传回的数据为：{}".format(buf))  # 断开连接时服务器会传空串，如果写在if前则输出两次
                # 处理传来是查询英文句子的情况
                if buf[0] == '0':
                    # 文件操作，并发并行写入文件时需要加锁
                    fileName = 'client.txt'
                    saveFile(buf=buf[1:], fileName=fileName)
            else:
                pass

        except ConnectionAbortedError:
            print('【提醒】服务器已关闭该链接')
            break
        except ConnectionResetError:
            print('【提醒】服务器已关闭')
            break


def sendData():
    while True:
        try:
            sample_data1 = "sentence:4,5,9#end"
            sample_data2 = "talk:你好吗？#end"
            print("【提醒】请输入要发给服务器的话，样例为 {} 以及 {}".format(sample_data1, sample_data2))
            data = input("")
            # 发送数据
            byteswritten = 0
            while byteswritten < len(data):
                startpos = byteswritten
                endpos = min(byteswritten + BUFFERSIZE, len(data))
                byteswritten += client.send(data[startpos:endpos].encode())
                print("【提醒】客户端一共发送了 %d bytes 给了服务器" % byteswritten)

        except ConnectionAbortedError:
            print('【提醒】服务器已关闭该链接')
        except ConnectionResetError:
            print('【提醒】服务器已关闭')


def recvData():
    # 接收数据
    while True:
        try:
            buf = client.recv(BUFFERSIZE).decode()
            if buf:
                print("【提醒】服务器传回的数据为：{}".format(buf))  # 断开连接时服务器会传空串，如果写在if前则输出两次
                # 处理传来是查询英文句子的情况
                if buf[0] == '0':
                    # 文件操作，并发并行写入文件时需要加锁
                    fileName = 'client.txt'
                    saveFile(buf=buf[1:], fileName=fileName)
            else:
                pass

        except ConnectionAbortedError:
            print('【提醒】服务器已关闭该链接')
        except ConnectionResetError:
            print('【提醒】服务器已关闭')


if __name__ == '__main__':
    '''
        Q：客户端发完一条消息，必须等服务器发一条回来才能继续发送，同时无法应对多个客户端
    '''
    # sendAndRecv()

    '''
        解决办法: 
            分开发送进程和接收进程，且用多线程机制执行它们，以避免Q中的input阻塞
    '''
    th1 = threading.Thread(target=sendData)
    th2 = threading.Thread(target=recvData)
    th1.start()
    th2.start()

