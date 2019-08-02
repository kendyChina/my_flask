# coding: utf-8

from flask import Flask, request, make_response
import hashlib, time, requests, sqlite3, logging
import xml.etree.ElementTree as ET

app = Flask(__name__)
access_token = None
logging.basicConfig(filename="log/my_app.log")

db = "db.db"

img_msg = """
	<xml>
		<ToUserName><![CDATA[%s]]></ToUserName>
		<FromUserName><![CDATA[%s]]></FromUserName>
		<CreateTime>%s</CreateTime>
		<MsgType><![CDATA[image]]></MsgType>
		<Image>
			<MediaId><![CDATA[%s]]></MediaId>
		</Image>
	</xml>
"""

text_msg = """
<xml>
	<ToUserName><![CDATA[%s]]></ToUserName>
	<FromUserName><![CDATA[%s]]></FromUserName>
	<CreateTime>%s</CreateTime>
	<MsgType><![CDATA[text]]></MsgType>
	<Content><![CDATA[%s暂无后台数据]]></Content>
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
		try:
			l.sort()
		except Exception:
			print(request.url)
		ll = ''.join(l)
		my_sha1 = hashlib.sha1(ll.encode("utf-8"))
		my_sign = my_sha1.hexdigest()
		if my_sign == signature:
			return echostr
		else:
			return False
	# 接收用户主动发送的信息
	else:

		xmlData = ET.fromstring(request.stream.read()) # 读取XML
		# msg_type = xmlData.find('MsgType').text
		ToUserName = xmlData.find('ToUserName').text # 用户信息的目的user
		FromUserName = xmlData.find('FromUserName').text # 用户信息的来源user
		content = xmlData.find('Content').text # 用户信息的内容

		with sqlite3.connect(db) as conn:
			c = conn.cursor()
			c.execute("SELECT media_id FROM key_media WHERE key=?", (content, ))
			try:
				media_id = c.fetchone()[0]
			except:
				media_id = None

		if media_id is not None: # 后台有该字段的数据
			resp = make_response(img_msg % (FromUserName, ToUserName, str(int(time.time())), media_id))
		else: # 暂无该字段数据
			resp = make_response(text_msg % (FromUserName, ToUserName, str(int(time.time())), content))
		resp.content_type = "application/xml"
		return resp

if __name__ == "__main__":
	app.run(host="0.0.0.0", port="80")
