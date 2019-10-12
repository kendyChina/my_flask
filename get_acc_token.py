# coding: utf-8

import requests, json, sqlite3, time
from my_flask.my_tools import get_gzh_passwd, Log

class GetToken(object):

	def __init__(self, url="https://api.weixin.qq.com/cgi-bin/token", appid="wxf9d2bfcde559934c", db="db.db"):
		# 获取access_token的url
		self.url = url
		# 微信开放平台的appid
		self.appid = appid
		# 数据库名称
		self.db = db
		# logger
		self.logger = Log(__name__).getlog()

	def run(self):

		with sqlite3.connect(self.db) as conn:
			c = conn.cursor()
			# 从数据库获取access_token和token_time
			c.execute("SELECT * FROM access_token")

			try:
				access_token, token_time = c.fetchone()
			except:
				token_time = float(0)
			else:
				token_time = float(token_time)

			# 如果现在超时时间前5分钟多，获取新的access_token
			if time.time() > token_time - 300:

				self.logger.info("token_time(%s)快超时了，正在尝试获取新access_token..." % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_time)), ))
				data = {
					# 获取access_token填写client_credential
					"grant_type": "client_credential",
					# 公众号id
					"appid": self.appid,
					# 公众号密码
					"secret": get_gzh_passwd()
				}

				headers = {
					"Content-Type": "application/json; encoding=utf-8"
				}

				resp = json.loads(requests.get(self.url, params=data, headers=headers).text)

				try:
					access_token = resp["access_token"]
					expires_in = resp["expires_in"]
				except Exception as e:
					self.logger.info(resp)
					self.logger.exception(e)
					access_token = None
					expires_in = None
				token_time = time.time() + expires_in

				# 删除原access_token和过期时间
				c.execute("""DELETE FROM access_token;""")
				# 插入新access_token和过期时间
				c.execute("""INSERT INTO access_token VALUES (?, ?);""", (access_token, token_time))
				self.logger("更新了access_token{}和token_time{}".format(access_token, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_time)),))
		return access_token

if __name__ == "__main__":
	GetToken().run()
