# coding: utf-8

import paramiko, os, time, hashlib, logging
import matplotlib.pyplot as plt
import pandas as pd


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

class DrawTableSave(object):

	def __init__(self, key, title, df, size_inches=(10.0/1.5, 15.0/1.5), colWidths=0.15, fontsize=18, title_x=0.35, target_path=r"img", target_format="jpg"):
		self.key = key
		self.title = title
		self.df = df
		self.size_inches = size_inches
		self.colWidths = colWidths
		self.fontsize = fontsize
		self.title_x = title_x
		self.target_path = target_path
		self.target_format = target_format

	def set_key(self, key):
		self.key = key

	def get_key(self):
		return self.key

	def set_title(self, title):
		self.title = title

	def get_title(self):
		return self.title

	def set_df(self, df):
		if isinstance(df, pd.DataFrame):
			self.df = df
		else:
			raise TypeError("df需为DataFrame，默认初始化时传入")

	def set_size_inches(self, size_inches):
		if isinstance(size_inches, tuple):
			self.size_inches = size_inches
			return True
		else:
			raise TypeError("size_inches需为tuple类型，默认(10.0/1.5, 15.0/1.5)")

	def set_colWidths(self, colWidths):
		try:
			self.colWidths = float(colWidths)
		except:
			raise TypeError("colWidths需为float类型，默认0.15")

	def set_fontsize(self, fontsize):
		try:
			self.fontsize = float(fontsize)
		except:
			raise TypeError("fontsize需为int或float类型，默认18")

	def set_title_x(self, title_x):
		try:
			self.title_x = float(title_x)
		except:
			raise TypeError("title_x需为int或float，默认0.35")

	def init_color(self):
		# 隔行设置row颜色：灰白相间
		self.rowcolor = []
		for i in range(len(self.df.index)):
			if i % 2 == 0:
				self.rowcolor.append("#DCDCDC")  # 浅灰
			else:
				self.rowcolor.append("white")

		# 隔行设置cell颜色：灰白相间
		self.cellcolor = []
		for i in range(len(self.df.index)):
			if i % 2 == 0:
				color = "#DCDCDC"  # 浅灰
			else:
				color = "white"
			self.cellcolor.append([color for x in range(len(self.df.columns))])

	def init_plt(self):
		# 初始化表格样式
		self.plt = plt
		self.plt.table(
			cellText=self.df.values,
			colLabels=self.df.columns,
			colWidths=[self.colWidths] * len(self.df.columns),
			rowLabels=self.df.index,
			loc="best",
			cellLoc="center",
			colLoc="center",
			rowLoc="center",
			rowColours=self.rowcolor,
			cellColours=self.cellcolor
		)

		# 关闭坐标轴
		self.plt.xticks([])
		self.plt.yticks([])

		self.plt.axis("off")

		# 设置标题
		self.plt.title(
			"%s(%s日)" % (self.title, time.strftime("%m-%d", time.localtime(time.time()))),
			fontsize=self.fontsize,
			verticalalignment="center",
			# horizontalalignment="left",
			fontweight="black",
			color="#000000",
			x=self.title_x
		)

	def draw_and_save(self):
		# 初始化图像尺寸
		self.plt.gcf().set_size_inches(*self.size_inches)
		target = os.path.join(self.target_path, r"%s.%s" % (self.key, self.target_format))  # 保存为jpg
		self.plt.savefig(target, bbox_inches="tight", pad_inches=0.5)
		return {self.key: target}

	def close(self):
		self.plt.close()

	def __del__(self):
		self.close()

class GetPasswd(object):

	def __init__(self, file_path, passwd_name):
		self.file_path = file_path
		self.passwd_name = passwd_name

	def get_it(self):
		if os.path.exists(self.file_path):
			with open(self.file_path) as f:
				passwd = f.readline().strip()
		else:
			passwd = input("请输入%s密码：", self.passwd_name)
		return passwd

def get_ssh_passwd():
	"""
    通过配置文件，
    获取ssh密码
    :return:
    """
	gp = GetPasswd("passwd/ssh_passwd.txt", "ssh")
	passwd = gp.get_it()
	return passwd

def get_gzh_passwd():
	"""
	获取公众号密码
	:return:
	"""
	gp = GetPasswd("passwd/gzh_passwd.txt", "gzh")
	passwd = gp.get_it()
	return passwd

def get_yan_passwd():
	"""
	获取加密用的yan
	:return:
	"""
	gp = GetPasswd("passwd/yan_passwd.txt", "yan")
	passwd = gp.get_it()
	return passwd

def to_md5(key):
	yan = get_yan_passwd()
	try:
		key = key.encode("utf-8")
		yan = yan.encode("utf-8")
	except:
		pass
	finally:
		key_md5 = hashlib.md5(key + yan)
		return key_md5.hexdigest()

def get_logger():
	# 配置logger
	logger = logging.getLogger("logger")

	handler1 = logging.StreamHandler()
	handler2 = logging.FileHandler(filename="log/scheduler.log", encoding="utf-8", mode="a+")

	logger.setLevel(logging.DEBUG)
	handler1.setLevel(logging.DEBUG)
	handler2.setLevel(logging.INFO)

	formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
	handler1.setFormatter(formatter)
	handler2.setFormatter(formatter)

	logger.addHandler(handler1)
	logger.addHandler(handler2)

	return logger

if __name__ == '__main__':
	print(to_md5("行业部达产通报"))