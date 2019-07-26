# coding: utf-8

from flask import Flask, request, make_response
import hashlib, time, requests, sqlite3
import xml.etree.ElementTree as ET
from my_flask.get_acc_token import get_token
from my_flask.jf import run_jf

app = Flask(__name__)
access_token = None

msg = """
	<xml>
	<ToUserName><![CDATA[%s]]></ToUserName>
	<FromUserName><![CDATA[%s]]></FromUserName>
	<CreateTime>%s</CreateTime>
	<MsgType><![CDATA[%s]]></MsgType>
	<Image>
   	 <MediaId><![CDATA[%s]]></MediaId>
  	</Image>
	</xml>
"""

@app.route("/", methods=["GET", "POST"])
def index():
	global token_time
	# 判断signature是否相同，由腾讯主动发起
	# 如相等则返回echostr
	if request.method == "GET":

		token = "kendy123"
		signature = request.args.get("signature")
		echostr = request.args.get("echostr")
		timestamp = request.args.get("timestamp")
		nonce = request.args.get("nonce")
		l = [token, timestamp, nonce]
		l.sort()
		ll = ''.join(l)
		my_sha1 = hashlib.sha1(ll.encode("utf-8"))
		my_sign = my_sha1.hexdigest()
		if my_sign == signature:
			# print(my_sign)
			return echostr
		else:
			# print(signature)
			# print(my_sign)
			return False
	# 接收用户主动发送的信息
	else:

		access_token = get_token().get_token()

		xmlData = ET.fromstring(request.stream.read())
		# msg_type = xmlData.find('MsgType').text
		msg_type = "image"
		ToUserName = xmlData.find('ToUserName').text
		FromUserName = xmlData.find('FromUserName').text
		xm = xmlData.find('Content').text

		with sqlite3.connect("db.db") as conn:
			c = conn.cursor()
			c.execute("SELECT media_id FROM xm_media WHERE xm=?", (xm, ))
			media_id = c.fetchone()
		print("msg_type: %s\nToUserName: %s\nFromUserName: %s\nMediaId: %s" % (msg_type, ToUserName, FromUserName, media_id))

		resp = make_response(
			msg % 
			(FromUserName, ToUserName, str(int(time.time())), msg_type, media_id)
		)
		resp.content_type = "application/xml"
		return resp

if __name__ == "__main__":
	app.run(host="0.0.0.0", port="80")
