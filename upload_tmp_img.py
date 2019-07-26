# coding: utf-8
import requests, json, sqlite3, os
from my_flask.get_acc_token import get_token

def upload_tmp_img():
	access_token = get_token().get_token()
	url = r"https://api.weixin.qq.com/cgi-bin/media/upload"
	xm_id = {}
	with sqlite3.connect("db.db") as conn:
		c = conn.cursor()
		c.execute("SELECT * FROM xm_img;")
		xm_img = c.fetchall()
		c.execute("DELETE FROM xm_media;")


		for xm, img in xm_img:

			data = {"media": img}
			resp = requests.post(url, data=data)

			params = {"access_token": access_token,"type": "image"}
			with open(img, "rb") as f:
				payload = f.read()
			content_type = "multipart/form-data"
			headers = {"Content-Type": content_type}
			data = {"data": (img, payload, content_type)}
			resp = requests.post(url, files=data, params=params, headers=headers)

			media_id = json.loads(resp.text)["media_id"]
			xm_id[xm] = media_id

			c.execute("INSERT INTO xm_media VALUES (?, ?)", (xm, media_id))
	print(xm_id)

if __name__ == "__main__":
	upload_tmp_img()
