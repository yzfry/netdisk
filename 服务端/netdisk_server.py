#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
@File    :   netdisk_server.py
@Time    :   2024/10/23 21:47
@Author  :   yzfry
@Desc    :   netdisk服务端
"""
import socket
import struct
import os
import select


#TODO 瞬间响应命令由主线程负责，上传下载命令由子线程负责

# 状态代码
"""
SUCCESS 成功
ERROR 错误
REGISTER 用户注册
REQUEST 瞬时响应的命令
REQUEST_FILE 上传下载命令
"""
SUCCESS = 1
ERROR = 0
REGISTER = 2
LOGIN = 3
REQUEST = 4
REQUEST_FILE = 5

def ask_status(ask_socket:socket.socket, status:int):
    """
    发送状态
    :param ask_socket: 发送的socket
    :param status: 状态
    :return:
    """
    ask_socket.sendall(struct.pack('>I', status))

def res_status(res_socket:socket.socket):
    """
    接收状态
    :param res_socket:socket
    :return: 状态代码
    """
    status_bytes = res_socket.recv(4)
    return struct.unpack('>I', status_bytes)[0]

# debug
DEBUG = True
def debug(tag, msg):
    if DEBUG:
        print('[%s] %s'% (tag, msg))

class User:
    """
    一个客户端就对应一个User实例化
    """
    def __init__(self, new_client, client_address):
        # 用户ip和端口号
        self.client_address = client_address
        # 用户连接
        self.client_socket:socket.socket = new_client
        self.username = None
        # 用户的token
        self.token = None
        # 储存用户的路径
        self.path = os.getcwd()

    def command_processing(self) -> bool:
        """
        接收用户命令，调用对应函数进行处理
        :return:返回用户是否断开
        """
        command_bytes = self.recv_data()
        # 如果是空数据则用户断开，返回false
        if not command_bytes:
            return False
        command = command_bytes.decode('utf-8')
        print(f"接收到命令{command}来自{self.client_address}")

        if command[:2] == 'ls':
            self.ls_processing(command)
        elif command[:2] == 'cd':
            pass
        elif command[:3] == 'pwd':
            self.pwd_processing(command)
        elif command[:2] == 'rm':
            pass
        elif command[:4] == 'puts':
            pass
        elif command[:4] == 'gets':
            print('gets')
            self.gets_processing(self.client_socket, command)
        elif command[:5] == 'mkdir':
            pass
        elif command[:5] == 'rmdir':
            pass
        else:
            print("wrong command:", command)
        # 正常处理，返回true
        return True

    def ls_processing(self, command):
        ls_data = str(self.client_address) + ''
        list_file = os.listdir(self.path)
        for file_name in list_file:
            # 拼接当前目录文件名和文件大小
            # todo 待完善
            ls_data += file_name + '\t\t\t\t' + str(os.path.getsize(self.path + '/' + file_name)) + '\n'
        # 发送给客户端
        self.send_data(ls_data.encode('utf-8'))

    def cd_processing(self, command):
        pass

    def pwd_processing(self, command):
        self.send_data(self.path.encode('utf-8'))

    def rm_processing(self, command):
        pass

    def puts_processing(self, command):
        pass

    def gets_processing(self, new_client_file: socket.socket, command):
        """
        传输文件协议
        :param new_client_file:专门用来传输文件的连接
        :param command:命令
        :return:
        """
        # command: gets file
        # 发送文件名
        file_name = command.split()[1]
        head_file_name = struct.pack('>I', len(file_name))
        file_name_bytes = file_name.encode('utf-8')
        new_client_file.send(head_file_name + file_name_bytes)

        # 发送文件大小
        file_size = os.stat(file_name).st_size
        new_client_file.send(struct.pack('>I', file_size))

        # 发送文件内容
        f = open(file_name, 'rb')
        while True:
            file_content = f.read(1024)
            if file_content:
                new_client_file.send(file_content)
            else:
                break
        f.close()


    def mkdir_processing(self, command):
        pass

    def rmdir_processing(self, command):
        pass

    def send_data(self, send_bytes):
        """
        自定义协议，防止粘包，就是防止两个数据包连在一起无法区分
        用于发送瞬时响应的命令
        :param send_bytes: 字节流数据
        :return: None
        """
        try:
            # 计算数据的长度，使用pack将长度整数变成4个字节字节流
            head_bytes = struct.pack('>I', len(send_bytes))
            # senddall会循环调用send函数,保证数据全部都发送出去
            # 将数据长度和数据发送给客户端
            self.client_socket.sendall(head_bytes + send_bytes)
        except Exception as msg:
            print(msg)

    def recv_data(self):
        """
        接收字节流
        用于接收瞬时响应的命令
        :return: 字节流
        """
        try:
            # 解包数据长度
            head_bytes = self.client_socket.recv(4)
            head_bytes_len = struct.unpack('>I', head_bytes)[0]
            return self.client_socket.recv(head_bytes_len)
        except Exception as msg:
            print(msg)

    def user_close(self):
        """
        关闭用户链接
        :return: None
        """
        self.client_socket.close()

class NetDiskServer:

    # 工作目录
    main_path = os.getcwd()

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server_socket = None
        # 存放用户连接socket的实例化user对象
        self.client_socket_list = []

    def tcp_init(self):
        """
        tcp初始化绑定端口，开启监听
        :return: None
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 确保端口复用
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.ip, self.port))
            self.server_socket.listen(125)
        except Exception as msg:
            debug('error', '初始化失败' + str(msg))

    def tcp_close(self):
        """
        关闭server_sock
        :return:
        """
        self.server_socket.close()

    def start(self):
        """
        主流程:accept连接，然后创建User对象，调用user.command_processing()接收处理命令
        :return: None
        """
        # 创建epoll
        epoll = select.epoll()
        # 监控server_socket
        epoll.register(self.server_socket.fileno(), select.EPOLLIN)

        while True:
            # 等待epoll返回有数据的缓冲区的列表
            epoll_list = epoll.poll()
            # 取出列表
            for fd, _ in epoll_list:
                # 如果是server_scoket则表示有用户连接或者用户请求文件操作
                if fd == self.server_socket.fileno():
                    new_client, client_address = self.server_socket.accept()
                    debug('info', '客户端{}连接'.format(client_address))
                    # 接收客户端状态
                    status = res_status(new_client)
                    # 创建用户实例
                    user = User(new_client, client_address)

                    # 用户登录
                    if status == LOGIN:
                        # 处理用户登录
                        status = self.login(user)
                        if status == SUCCESS:
                            # 发送登录成功
                            ask_status(new_client, status)
                            # 注册成功则把新连接用户的实例化user放入列表并监控
                            self.client_socket_list.append(user)
                            epoll.register(user.client_socket.fileno(), select.EPOLLIN)
                        else:
                            debug('warning', '用户{}登录失败'.format(client_address))
                            ask_status(user.client_socket, status)
                    # 用户注册
                    elif status == REGISTER:
                        pass
                    # 用户请求文件操作需要验证token
                    elif status == REQUEST:
                        pass

                else:
                    # 如果是某个用户则处理命令
                    for user in self.client_socket_list:
                        if user.client_socket.fileno() == fd:
                            ret = user.command_processing()
                            # 如果用户断开，则区列表一处，并且注销
                            if not ret:
                                print(len(self.client_socket_list))
                                print(f'{user.client_address}断开')
                                self.client_socket_list.remove(user)
                                epoll.unregister(user.client_socket.fileno())

    def login(self, user: User):
        # 接收账号和密码
        username = user.recv_data()
        password = user.recv_data()
        # TODO 数据库验证待添加
        pass
        # TODO 生成用户token
        user.token = '49217407'
        user.username = username
        return SUCCESS



    def register(self, new_client:socket.socket):
        pass


if __name__ == '__main__':
    netdistserver = NetDiskServer("", 2333)
    netdistserver.tcp_init()
    netdistserver.start()