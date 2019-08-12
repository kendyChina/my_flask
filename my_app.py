# coding: utf-8

from flask import Flask, request, make_response
import hashlib, time, sqlite3, requests, json
import xml.etree.ElementTree as ET
from my_flask.my_tools import get_logger
from my_flask.get_acc_token import get_token

app = Flask(__name__)
access_token = None

logger = get_logger()

db = "db.db"

def get_callback_ip():
	url = "https://api.weixin.qq.com/cgi-bin/getcallbackip"
	params = {"access_token": get_token()}
	resp = requests.get(url, params)
	ip_list = json.loads(resp.content.decode("utf-8"))["ip_list"]
	return ip_list


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
	<Content><![CDATA[%s]]></Content>
</xml>
"""

@app.route("/", methods=["GET", "POST"])
def index():
	global token_time
	# 判断signature是否相同，由腾讯主动发起
	# 如相等则返回echostr
	if request.method == "GET":

		if request.url in get_callback_ip():
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
				logger.info("my_sign == signature，返回echostr")
				return echostr
			else:
				logger.info("my_sign != signature，返回False")
				return False
		else:
			logger.info("url不在ip_list中：method=%s，url=%s，path=%s，args=%s" % (request.method, request.url, request.path, request.args.to_dict()))
			return False
	# 接收用户主动发送的信息
	else:

		xmlData = ET.fromstring(request.stream.read()) # 读取XML
		msg_type = xmlData.find("MsgType").text
		ToUserName = xmlData.find("ToUserName").text # 用户信息的目的user
		FromUserName = xmlData.find("FromUserName").text # 用户信息的来源user

		if msg_type == "text":
			content = xmlData.find("Content").text  # 用户信息的内容
			with sqlite3.connect(db) as conn:
				c = conn.cursor()
				c.execute("SELECT media_id FROM key_media WHERE key=?", (content, ))
				try:
					media_id = c.fetchone()[0]
				except:
					media_id = None

			if media_id is not None: # 后台有该字段的数据
				my_content = img_msg % (FromUserName, ToUserName, str(int(time.time())), media_id)
				resp = make_response(my_content)
				logger.info("后台有数据：FromUserName=%s，MsgType=%s，Content=%s" % (FromUserName, msg_type, content))
			else: # 暂无该字段数据
				my_content = text_msg % (FromUserName, ToUserName, str(int(time.time())), content + "暂无后台数据")
				resp = make_response(my_content)
				logger.info("后台无数据：FromUserName=%s，MsgType=%s，Content=%s" % (FromUserName, msg_type, content))
		elif msg_type == "event":
			event = xmlData.find("Event").text  # 事件内容
			if event == "subscribe":
				my_content = "感谢您的关注，请回复进行测试：\n8a83871129c8d4809581ae156ddbb78e"
				resp = make_response(text_msg % (FromUserName, ToUserName, str(int(time.time())), my_content))
				logger.info("新增订阅：FromUserName=%s，MsgType=%s，Event=%s" % (FromUserName, msg_type, event))
			elif event == "unsubscribe":
				logger.info("减少订阅：FromUserName=%s，MsgType=%s，Event=%s" % (FromUserName, msg_type, event))
		else:
			my_content = text_msg % (FromUserName, ToUserName, str(int(time.time())), "系统有bug...")
			resp = make_response(my_content)
			logger.info("msg_type匹不上：FromUserName=%s，msg_type=%s" % (FromUserName, msg_type))

		resp.content_type = "application/xml"
		return resp

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=80)
