# coding: utf-8

import requests, json, sqlite3, time, os

class get_token(object):

	def __init__(self, url="https://api.weixin.qq.com/cgi-bin/token", appid="wxf9d2bfcde559934c", acc_db = "db.db", acc_table = "access_token"):
		self.url = url
		self.appid = appid
		self.acc_db = acc_db
		self.acc_table = acc_table

	def get_passwd(self):
		my_dir = os.path.dirname(os.path.realpath(__file__))
		passwd_name = "passwd.txt"
		passwd_file = os.path.join(my_dir, passwd_name)
		if os.path.exists(passwd_file):
			with open(passwd_file, "r") as f:
				passwd = f.readline().strip()
		else:
			passwd = input("请输入公众号密码：")
		print("passwd: %s" % passwd)
		return passwd

	def get_token(self):
		with sqlite3.connect(self.acc_db) as conn:
			c = conn.cursor()
			c.execute("SELECT * FROM %s" % (self.acc_table, ))

			access_token, token_time = c.fetchone()
			token_time = float(token_time)

			# 如果现在超时时间前5分钟多，获取新的access_token
			if time.time() > token_time - 300:

				print("token_time(%s)快超时了，正在尝试获取新access_token..." % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_time)), ))
				data = {}
				data["grant_type"] = "client_credential"
				data["appid"] = self.appid
				data["secret"] = self.get_passwd()

				headers = {}
				headers["Content-Type"] = "application/json; encoding=utf-8"

				resp = requests.get(self.url, params=data)
				# json化
				resp = json.loads(resp.text)
				print(resp)
				access_token = resp["access_token"]
				expires_in = resp["expires_in"]
				token_time = time.time() + expires_in

				# 删除原access_token和过期时间
				c.execute("""DELETE FROM access_token;""")
				# 插入新access_token和过期时间
				c.execute("""INSERT INTO access_token
					VALUES (?, ?);""", (access_token, token_time))

				print("Has update access_token(%s) and token_time(%s)" % (access_token, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_time)),))
		return access_token

if __name__ == "__main__":
	a = get_token()
	a.get_passwd()
