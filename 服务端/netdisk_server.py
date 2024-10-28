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


class NetDiskServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server_sock = None

    def tcp_init(self):
        """
        tcp初始化绑定端口，开启监听
        :return: None
        """
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 使端口快速重用
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind((self.ip, self.port))
            self.server_sock.listen(125)
        except Exception as msg:
            print(msg)

    def tcp_close(self):
        """
        关闭server_sock
        :return:
        """
        self.server_sock.close()

    def start(self):
        """
        主流程:accept连接，然后创建User对象，调用user.command_processing()接收处理命令
        :return: None
        """
        new_client, client_address = self.server_sock.accept()
        print(f"用户连接{client_address}")
        user = User(new_client, client_address)
        # 接收处理客户端发来的命令
        user.command_processing()


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
        # 储存用户的路径
        self.path = os.getcwd()

    def command_processing(self):
        """
        接收用户命令，调用对应函数进行处理
        :return:
        """
        # 循环接收用户命令
        while True:
            command = self.recv_data().decode('utf-8')
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

    def ls_processing(self, command):
        ls_data = ''
        list_file = os.listdir(self.path)
        for file_name in list_file:
            # 拼接当前目录文件名和文件大小
            # todo 待完善
            ls_data += file_name + '\t\t\t\t' + str(os.path.getsize(self.path + '\\' + file_name)) + '\n'
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



if __name__ == '__main__':
    netdistserver = NetDiskServer("", 8080)
    netdistserver.tcp_init()
    netdistserver.start()