# coding: utf-8
import requests, json, sqlite3, os
from my_flask import get_acc_token

url = r"https://api.weixin.qq.com/cgi-bin/media/upload"
db = "db.db"

def upload_tmp_img():
	access_token = get_acc_token.get_token()

	key_id = {}
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("SELECT * FROM key_img;") # 获取key_img数据库中所有的对应关系
		key_img = c.fetchall()
		c.execute("DELETE FROM key_media;") # 删除key_media数据库中所有信息

		for key, img in key_img:

			params = {"access_token": access_token,"type": "image"}
			with open(img, "rb") as f:
				payload = f.read()
			content_type = "multipart/form-data"
			headers = {"Content-Type": content_type}
			data = {"data": (img, payload, content_type)}
			resp = requests.post(url, files=data, params=params, headers=headers) # files存放img内容，params存放url标识

			try:
				media_id = json.loads(resp.text)["media_id"]
			except Exception as e:
				print(e)
			key_id[key] = media_id

			c.execute("INSERT INTO key_media VALUES (?, ?)", (key, media_id)) # 把key和media_id记录到数据库

if __name__ == "__main__":
	upload_tmp_img()
