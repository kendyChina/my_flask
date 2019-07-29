# my_flask.py

项目实现的是在公众号发送项目名称，公众号自动回复项目转化情况表图。

# db.db

包含三个表：access_token、xm_img、xm_media

access_token含token、time字段。
token为access_token，time为超时时间。

xm_img含xm、img字段。
xm为项目名称，img为图片路径。

xm_media含xm、media_id字段。
xm为项目名称，media_id为微信公众平台临时素材id。

# jf.py

读取经分的csv明细（来源总商），通过pandas库对数据进行处理，通过matplotlib库进行绘制并保存为jpg图片。
并把xm和img的对应关系存放在xm_img表中。

# get_acc_token.py

先从access_token表获取access_token，如果快过期了（超时时间5分钟以内），就重新获取，并写入表中。

# upload_tmp_img.py

从xm_img表中获取xm和img的对应关系，逐一上传到微信公众平台的临时素材中，
并把返回的media_id及与之对应的xm添加到xm_media表中。

# my_app.py

接收用户信息，提取内容字段，如果内容（项目）在xm_media表中查询得，则通过media_id返回项目图片，
反之则声明暂无后台数据。