#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
@File    :   netdisk_client.py
@Time    :   2024/10/23 21:45
@Author  :   yzfry
@Desc    :   netdisk客户端
"""
import socket
import struct
import sys

# 状态代码
SUCCESS = 1
ERROR = 0
REGISTER = 2
LOGIN = 3
REQUEST = 4
REQUEST_FILE = 5


def ask_status(ask_socket:socket.socket, status:int):
    ask_socket.sendall(struct.pack('>I', status))

def res_status(res_socket:socket.socket):
    status_bytes = res_socket.recv(4)
    return struct.unpack('>I', status_bytes)[0]


class Client:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client_socket = None
        # 储存接收到的token
        self.token = None

    def connect(self):
        """
        连接服务端
        :return:
        """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.ip, self.port))

    def login(self):
        choose = int(input('登录0 注册1 >'))
        if choose == 0:
            # 告诉服务端要登录
            ask_status(self.client_socket, LOGIN)
            # 用户输入账号和密码
            username = str(input('[登陆]username >'))
            password = str(input('[注册]password >]'))
            # 发送用户名和密码到服务端
            self.send_data(username.encode('utf-8'))
            self.send_data(password.encode('utf-8'))

            if res_status(self.client_socket) == SUCCESS:
                print('[登录成功]')
            else:
                print('[登录失败]')
                self.user_close()

        elif choose == 1:
            pass

    def send_command(self):
        while True:
            command = input('>')
            self.send_data(command.encode('utf-8'))
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
                self.gets_processing(self.client_socket,command)
            elif command[:5] == 'mkdir':
                pass
            elif command[:5] == 'rmdir':
                pass
            else:
                print("wrong command:", command)

    def ls_processing(self, command):
        ls_data = self.recv_data().decode('utf-8')
        print("文件名\t\t\t\t文件大小")
        # 输出时删除最后一个\n
        print(ls_data[:-2])

    def cd_processing(self, command):
        pass

    def pwd_processing(self, command):
        data = self.recv_data().decode('utf-8')
        print(data)

    def rm_processing(self, command):
        pass

    def puts_processing(self, command):
        pass

    def gets_processing(self,new_client_file: socket.socket, command):
        # 接收文件名
        head_file_name = new_client_file.recv(4)
        file_name_len = struct.unpack('>I', head_file_name)[0]
        file_name = new_client_file.recv(file_name_len)

        # 接收文件大小
        file_size_bytes = new_client_file.recv(4)
        file_size = struct.unpack('>I', file_size_bytes)[0]

        # 循环接收文件
        f = open(file_name, 'wb')
        # 记录接收到的字节
        total = 0
        while total < file_size:
            # 这里有个问题就是recv(1024)即使服务端发送的1024字节的数据还没到全，只到了600字节也会返回600字节，因此需要循环接收
            data = new_client_file.recv(1024)
            if not data:
                # 如果没有recv到数据，说明服务端断开
                break
            f.write(data)
            total += len(data)
            # 进度条
            percentage = round(total / file_size * 100)
            print("\r进度: {}%: ".format(percentage), '[', "-" * (percentage // 2), ']', end='')
            sys.stdout.flush()
        print('')
        f.close()


    def mkdir_processing(self, command):
        pass

    def rmdir_processing(self, command):
        pass

    def send_data(self, send_bytes):
        """
        自定义协议，防止粘包
        :param send_bytes: 字节流数据
        :return: None
        """
        try:
            head_bytes = struct.pack('>I', len(send_bytes))
            self.client_socket.sendall(head_bytes + send_bytes)
        except Exception as msg:
            print(msg)

    def recv_data(self):
        """
        接收字节流
        :return: 字节流
        """
        try:
            head_bytes = self.client_socket.recv(4)
            head_bytes_len = struct.unpack('>I', head_bytes)[0]
            return self.client_socket.recv(head_bytes_len)
        except Exception as msg:
            print(msg)

    def user_close(self):
        self.client_socket.close()

if __name__ == '__main__':
    client = Client("192.168.232.142", 2333)
    client.connect()
    client.login()
    client.send_command()