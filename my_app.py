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
	<Content><![CDATA[%s]]></Content>
	</xml>
"""

xm_img = run_jf()

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

		# 如果当前时间在超时的5分钟内
		with sqlite3.connect("db.db") as conn:
			c = conn.cursor()
			c.execute("""select * from access_token""")
			access_token, tokentime = c.fetchone()
		if time.time() > tokentime - 300:
			access_token = get_token().get_token()

		xmlData = ET.fromstring(request.stream.read())
		msg_type = xmlData.find('MsgType').text
		ToUserName = xmlData.find('ToUserName').text
		FromUserName = xmlData.find('FromUserName').text
		Content = xmlData.find('Content').text
		print("msg_type: %s\nToUserName: %s\nFromUserName: %s\nContent: %s" % (msg_type, ToUserName, FromUserName, Content))
		# signature = request.args.get("signature")
		# timestamp = request.args.get("timestamp")
		# nonce = request.args.get("nonce")
		# openid = request.args.get("openid")
		resp = make_response(
			msg % 
			(FromUserName, ToUserName, str(int(time.time())), msg_type, Content)
		)
		resp.content_type = "application/xml"
		return resp


		

if __name__ == "__main__":
	app.run(host="0.0.0.0", port="80")
