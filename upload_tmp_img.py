# coding: utf-8
import requests, json, sqlite3
from my_flask.get_acc_token import get_token
from my_flask.my_tools import to_md5, get_logger

url = r"https://api.weixin.qq.com/cgi-bin/media/upload"
db = "db.db"

logger = get_logger()

def upload_tmp_img():
	access_token = get_token()

	key_id = {}
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		# 获取key_img数据库中所有的对应关系
		c.execute("SELECT * FROM key_img;")
		key_img = c.fetchall()
		# 删除key_media数据库中所有信息
		c.execute("DELETE FROM key_media;")

		for key, img in key_img:

			params = {"access_token": access_token, "type": "image"}
			with open(img, "rb") as f:
				payload = f.read()
			content_type = "multipart/form-data"
			headers = {"Content-Type": content_type}
			data = {"data": (img, payload, content_type)}
			# files存放img内容，params存放url标识
			resp = requests.post(url, files=data, params=params, headers=headers)

			try:
				media_id = json.loads(resp.text)["media_id"]
			except Exception as e:
				print(e)
			key_id[key] = media_id
			# 把key和media_id记录到数据库
			c.execute("INSERT INTO key_media VALUES (?, ?)", (key, media_id))
			logger.debug("%s获取media_id成功，并成功插入数据库", key)
		logger.info("media_id获取成功，并成功插入数据库")

if __name__ == "__main__":
	upload_tmp_img()
