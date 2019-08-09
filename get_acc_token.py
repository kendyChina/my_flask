# coding: utf-8

import requests, json, sqlite3, time
from my_flask.my_tools import get_gzh_passwd, get_logger

logger = get_logger()

def get_token():
	url = "https://api.weixin.qq.com/cgi-bin/token"  # 获取access_token的url
	appid = "wxf9d2bfcde559934c"  # 公众号appid
	db = "db.db"  # 数据库名称
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("SELECT * FROM access_token") # 从数据库获取access_token和token_time

		try:
			access_token, token_time = c.fetchone()
		except:
			token_time = float(0)
		else:
			token_time = float(token_time)

		# 如果现在超时时间前5分钟多，获取新的access_token
		if time.time() > token_time - 300:

			logger.info("token_time(%s)快超时了，正在尝试获取新access_token..." % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_time)), ))
			data = {
				"grant_type": "client_credential", # 获取access_token填写client_credential
				"appid": appid, # 公众号id
				"secret": get_gzh_passwd() # 公众号密码
			}

			headers = {
				"Content-Type": "application/json; encoding=utf-8"
			}

			resp = json.loads(requests.get(url, params=data, headers=headers).text)

			try:
				access_token = resp["access_token"]
				expires_in = resp["expires_in"]
			except Exception as e:
				logger.debug(resp)
				access_token = None
				expires_in = None
			token_time = time.time() + expires_in

			c.execute("""DELETE FROM access_token;""") # 删除原access_token和过期时间
			c.execute("""INSERT INTO access_token VALUES (?, ?);""", (access_token, token_time)) # 插入新access_token和过期时间
			print("Has updated access_token(%s) and token_time(%s)" % (access_token, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(token_time)),))
	return access_token

if __name__ == "__main__":
	get_token()
