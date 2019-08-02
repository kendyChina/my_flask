# coding: utf-8

import paramiko

def to_str(bytes_or_str):
    """
    把bytes转换成str
    :param bytes_or_str:
    :return: value
    """
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode("utf-8")
    else:
        value = bytes_or_str
    return value

class SSHConnection(object):

    def __init__(self, host_dict):
        self.host = host_dict['host']
        self.port = host_dict['port']
        self.username = host_dict['username']
        self.passwd = host_dict['passwd']
        self.__k = None

    def connect(self):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.passwd)
        self.__transport = transport

    def close(self):
        self.__transport.close()

    def run_cmd(self, command):
        ssh = paramiko.SSHClient()
        ssh._transport = self.__transport

        stdin, stdout, stderr = ssh.exec_command(command)

        resp = to_str(stdout.read())

        error = to_str(stderr.read())
        # 提交远端错误
        if error.strip():
            raise BaseException(error)
        return resp

    def upload(self, local_file, remote_file):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)

        sftp.put(local_file, remote_file, confirm=True)
        # 增加权限
        # 0o开头是八进制
        sftp.chmod(remote_file, 0o755)

    def download(self, remote_file, local_file):
        sftp = paramiko.SFTPClient.from_transport(self.__transport)
        sftp.get(remote_file, local_file)

    # 销毁
    def __del__(self):
        self.close()