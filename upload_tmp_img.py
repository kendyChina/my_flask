# coding: utf-8
import requests, json, sqlite3, os
from my_flask.get_acc_token import get_token

url = r"https://api.weixin.qq.com/cgi-bin/media/upload"
db = "db.db"

def upload_tmp_img():
	access_token = get_token()

	xm_id = {}
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("SELECT * FROM xm_img;") # 获取xm_img数据库中所有的对应关系
		xm_img = c.fetchall()
		c.execute("DELETE FROM xm_media;") # 删除xm_media数据库中所有信息

		for xm, img in xm_img:

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
			xm_id[xm] = media_id

			c.execute("INSERT INTO xm_media VALUES (?, ?)", (xm, media_id)) # 把xm和media_id记录到数据库
	print(xm_id)

if __name__ == "__main__":
	upload_tmp_img()
