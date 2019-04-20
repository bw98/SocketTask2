# coding=utf-8

# 本程序用于服务器练习
# 在 tcp 连接中，server 负责启动一个ip和端口，在这个端口监听，
# 当有 client 请求该监听端口时，开启一个新端口与 client 进行连接

# socket 启动监听的过程
# 1. create a socket
# 2. bind port
# 3. start listening
# 4. establish connection and keep listening

import re
import socket
from concurrent.futures import ThreadPoolExecutor


# 用于读取文件句子的类
class SentenceUtil:
    sentence = []

    def __init__(self):
        self.my_sentence = []  # 需要读取多个文件对象时则实例化并使用 my_sentence

    @classmethod
    def getSentence(cls):
        return cls.sentence

    @classmethod
    def setSentenceByFile(cls, file_name='English900.txt'):
        # 读取英语900文本
        with open(file_name, 'r') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                cls.sentence.append(line)

    def getMySentence(self):
        return self.my_sentence

    def setMySentence(self):
        return self.my_sentence


class ClientTask:

    def __init__(self, client, client_ip_and_port):
        self.client = client
        self.client_ip_and_port = client_ip_and_port
        self.encoding = 'utf-8'
        self.buffersize = 1024
        self.string = ''
        self.end = '#end'

    # string getter
    @property
    def string(self):
        return self._string

    # string setter
    @string.setter
    def string(self, value):
        if not isinstance(value, str):
            raise TypeError('客户端传来的数据不是一个字符串')
        self._string = value

    # 判断空串法，针对一次连接的数据接收方法，结果保存到 self.string
    def recvDataByInstantLink(self):
        total_data = []
        while True:
            data = self.client.recv(self.buffersize).decode()
            if data:  # 根据最后客户端的空串判断是否结束
                total_data.append(data)
            else:
                break
        self.string = ''.join(total_data)

    # 尾标识法，针对长连接的数据接收方法，结果保存到 self.string
    def recvDataByLongLink(self):
        total_data = []
        data = ''
        while True:
            # 情况一：客户端一行说完想要发送的hauteur
            data = self.client.recv(self.buffersize).decode()
            if self.end in data:
                total_data.append(data[:data.find(self.end)])
                break

            # 情况二：客户端分多行说完想要发送的话，并在最后才加入尾标识
            total_data.append(data)
            if len(total_data) > 1:
                last_pair = total_data[-2] + total_data[-1]
                if self.end in last_pair:
                    total_data.pop()
                    total_data[-2] = last_pair[:last_pair.find(self.end)]
                    break
        self.string = ''.join(total_data)

    def doEnglish(self, string):
        string = string[9:]
        send_data = ''
        if not re.match('[^0-9,]', string):
            sentence = SentenceUtil.getSentence()
            num_list = string.split(',')
            for item in num_list:
                if (int(item) - 1) < len(sentence):
                    send_data = send_data + sentence[int(item) - 1]  # 句子编号比行数多1
        return send_data

    def doTalk(self):
        send_data = ''
        print(('【提醒】请输入要发给客户端{}的话：'.format(self.client_ip_and_port)))
        string = input('>')
        send_data = send_data + string
        return send_data

    def doAutoTalk(self, string):
        send_data = ''
        string = str(string[5:])
        # 处理人称呼
        if string.count('你') > 0:
            string = string.replace('你', '我')
        # 处理问号
        if string.count('?') > 0:
            string = string.replace('?', '!')
        if string.count('？') > 0:
            string = string.replace('？', '！')
        # 处理停词
        if (string.count('吗') > 0) or (string.count('么') > 0) or (string.count('鸭') > 0) or (string.count('呀') > 0) or (
                string.count('干嘛') > 0 or (string.count('啊') > 0)):
            string = string.replace('吗', '')
            string = string.replace('么', '')
            string = string.replace('鸭', '')
            string = string.replace('呀', '')
            string = string.replace('啊', '')
            string = string.replace('干嘛', '')
        send_data = send_data + string
        return send_data

    def sendData(self, send_data, flag):
        if (send_data != '') and (flag != -1):
            byteswritten = 0
            if byteswritten < len(send_data):
                start_pos = byteswritten
                end_pos = min(byteswritten + self.buffersize, len(send_data))
                self.client.send((str(flag) + send_data[start_pos:end_pos]).encode())
                print("【提醒】发送信息给客户端成功，内容为{}".format(str(flag) + send_data[start_pos:end_pos]))
        else:
            send_data = str(flag) + '错误格式，正确格式为 sentence：#id, #id, #id #end 或 talk: 内容 #end'
            self.client.send(send_data.encode())

    # 唯一运行接口
    def run(self):
        try:
            while True:
                self.recvDataByLongLink()
                print('【提醒】从客户端 {} 接收的数据为{},长度为{}\n'.format(self.client_ip_and_port, self.string, len(self.string)))

                send_data = ''
                front_flag = -1  # -1 出错状态， 0 查句子业务状态，1 对话状态， 2退出状态
                if (self.string.find('goodbye') == 0) or (self.string.find('exit') == 0):
                    front_flag = 2
                    send_data = send_data + ' 您已断开和服务器的连接'
                    print('【提醒】客户端 {} 已退出'.format(self.client_ip_and_port))
                elif self.string[:9] == 'sentence:':  # 测试接受的数据头部是否为 sentence:
                    front_flag = 0
                    send_data = send_data + self.doEnglish(string=self.string)
                elif self.string[:5] == 'talk:':
                    front_flag = 1
                    send_data = send_data + self.doTalk()

                self.sendData(send_data=send_data, flag=front_flag)
                if front_flag == 2:
                    break
            self.client.close()
            print('【提醒】关闭客户端 {} 成功'.format(self.client_ip_and_port))

        except Exception as e:
            print("【提醒】出错了，原因为：{}\n将关闭客户端{}\n".format(e, self.client_ip_and_port))
            self.client.close()


class Listener:

    def __init__(self, ipAddr='127.0.0.1', port=12345):
        self.port = port
        self.ip = ipAddr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM,
                                  0)  # AF_INET 表示用IPV4地址族，SOCK_STREAM 是说是要是用流式套接字 0 是指不指定协议类型，系统自动根据情况指定
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ipAddr, port))
        self.sock.listen(10)  # WIN和MAC需要设置最大连接数量
        self.ENCODING = 'utf-8'
        self.BUFFERSIZE = 1024

    def run(self):
        print("TCP SERVER start...")
        print("host:{}, port:{}".format(self.ip, self.port))

        pool = ThreadPoolExecutor(10)  # 线程池最大线程数量

        # 接受客户端数据并响应，多线程处理以支持多个客户端
        while True:
            print("阻塞中，等待来自客户端的连接：")
            client, client_ip_and_port = self.sock.accept()  # 接受客户端请求之前保持阻塞
            clientTask = ClientTask(client, client_ip_and_port)
            pool.submit(clientTask.run)


if __name__ == '__main__':
    server_addr = socket.gethostbyname(socket.gethostname())  # 将host作为服务器ip地址
    server_port = 12233
    SentenceUtil.setSentenceByFile()  # 获取文件中的句子并初始化sentence类变量
    listener = Listener()
    listener.run()
