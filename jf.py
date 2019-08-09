# coding: utf-8

import time, datetime
import pandas as pd
import seaborn as sns
import sqlite3
from my_flask.my_tools import DrawTableSave, to_md5, get_logger
# 明细路径
mx_file = r"csv/jf.csv"
# 输出目标文件夹
target_path = r"img"
# 设置字体风格
sns.set_style({"font.sans-serif": ["simhei", "Arial"]})
# 数据库名称
db = "db.db"
# 读取csv文件
jf = pd.read_csv(mx_file, encoding="gbk")
# 初始化logger
logger = get_logger()

# 增加辅助字段
jf["外部下单日期"] = jf["外部下单时间"].map(lambda x: str(x)[:10]) # 获取外部下单日期，前十位
jf["激活日期"] = jf["入网时间"].map(lambda x: str(x)[:10]) # 获取激活日期，前十位
jf["首次充值日期"] = jf["首次充值时间"].map(lambda x: str(x)[:10]) # 获取首充日期，前十位
jf["首充≥50"] = jf["首次充值金额"].map(lambda x: "是" if x >= 50 else None) # 判断首充≥50
jf["激活月份"] = jf["激活月份"].map(lambda x: str(x)[:6])
jf["充值月份"] = jf["充值月份"].map(lambda x: str(x)[:6])

xm_set = set(jf["项目"]) # 项目set
hyb_set = set(jf["行业部"]) # 行业部set

def get_two_month_dates():
	"""
	获取本月的年月
	:return:
	"""
	this_year = datetime.datetime.now().year
	this_month = datetime.datetime.now().month

	# 获取本月的第一天和今天
	this_first_day = datetime.date(this_year, this_month, 1)
	this_today = time.strftime("%Y-%m-%d", time.localtime())

	# 获取上月的最后一天
	prev_last_day = this_first_day - datetime.timedelta(days=1)

	# 通过上月的最后一天获取上月的年月
	prev_year = str(prev_last_day.year)
	prev_month = str(prev_last_day.month).zfill(2)
	prev_year_month = prev_year + prev_month # yyyymm
	prev_first_day = prev_year + "-" + prev_month # yyyy-mm

	# 获取本月的日期索引
	this_dates = pd.date_range(start=this_first_day, end=this_today).strftime("%Y-%m-%d")

	return (this_dates, prev_year_month, prev_first_day)

def get_table(head, key):

	mx = jf[jf[head] == key] # 明细

	this_dates, prev_year_month, prev_first_day = get_two_month_dates()
	colunms = ["订单量", "激活量", "激活率", "首充≥50", "充值率", "综转率", "当日激活", "当日产能"]
	index = "%s月汇总" % prev_first_day[-2:]
	prev_df = pd.DataFrame(data=None, index=[index, ], columns=colunms)

	month_df = mx["下单月份"] == prev_first_day
	prev_df.loc[index, "订单量"] = mx[month_df]["外部订单号"].count()
	prev_df.loc[index, "激活量"] = mx[month_df]["入网时间"].count()
	prev_df.loc[index, "首充≥50"] = mx[month_df]["首充≥50"].count()
	prev_df.loc[index, "当日激活"] = mx[mx["激活月份"] == prev_year_month]["激活月份"].count()
	prev_df.loc[index, "当日产能"] = mx[mx["充值月份"] == prev_year_month]["充值月份"].count()

	try:
		prev_df["激活率"] = (prev_df["激活量"] / prev_df["订单量"]).apply(lambda x: format(x, ".2%"))
		prev_df["充值率"] = (prev_df["首充≥50"] / prev_df["激活量"]).apply(lambda x: format(x, ".2%"))
		prev_df["综转率"] = (prev_df["首充≥50"] / prev_df["订单量"]).apply(lambda x: format(x, ".2%"))
	except:
		prev_df["激活率"] = format(0, ".2%")
		prev_df["充值率"] = format(0, ".2%")
		prev_df["综转率"] = format(0, ".2%")

	this_df = pd.DataFrame(data=None, index=this_dates, columns=colunms)
	for date in this_dates:
		date_df = mx["外部下单日期"] == date
		this_df.loc[date, "订单量"] = mx[date_df]["外部订单号"].count()
		this_df.loc[date, "激活量"] = mx[date_df]["入网时间"].count()
		this_df.loc[date, "首充≥50"] = mx[date_df]["首充≥50"].count()
		this_df.loc[date, "当日激活"] = mx[mx["激活日期"] == date]["激活日期"].count()
		this_df.loc[date, "当日产能"] = mx[mx["首次充值日期"] == date]["首充≥50"].count()
	this_df.loc["%s月汇总" % this_dates[0][5:7]] = this_df.apply(lambda x: x.sum())
	try:
		this_df["激活率"] = (this_df["激活量"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
		this_df["充值率"] = (this_df["首充≥50"] / this_df["激活量"]).apply(lambda x: format(x, ".2%"))
		this_df["综转率"] = (this_df["首充≥50"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
	except:
		this_df["激活率"] = format(0, ".2%")
		this_df["充值率"] = format(0, ".2%")
		this_df["综转率"] = format(0, ".2%")

	df = prev_df.append(this_df)
	return df

def get_hyb_total():
	"""
	获取行业部整体通报
	:return:
	"""
	columns = ["已上线项目(电渠)", "昨日订单(电渠)", "本月总订单(电渠)", "昨日产能(电渠)", "本月总产能(电渠)", "本月日均产能(电渠)", "其中:中高端(电渠)", "本月电渠占比", "时序进度",
			   "昨日订单(整体)", "本月总订单(整体)", "昨日产能(整体)", "本月总产能(整体)", "本月日均产能(整体)"]
	index = set(jf["行业部"])
	df = pd.DataFrame(data=None, index=index, columns=columns)

	for hyb in index:
		yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
		df.loc[hyb, "昨日订单(整体)"] = jf[(jf["行业部"] == hyb) & (jf["外部下单日期"] == yesterday)]["外部订单号"].count()
		this_month = datetime.datetime.now().strftime("%Y-%m")
		df.loc[hyb, "本月总订单(整体)"] = jf[(jf["行业部"] == hyb) & (jf["下单月份"] == this_month)]["外部订单号"].count()
		df.loc[hyb, "昨日产能(整体)"] = jf[(jf["行业部"] == hyb) & (jf["激活日期"] == yesterday)]["外部订单号"].count()
		this_month2 = datetime.datetime.now().strftime("%Y%m")
		df.loc[hyb, "本月总产能(整体)"] = jf[(jf["行业部"] == hyb) & (jf["激活月份"] == this_month2)]["外部订单号"].count()
		df.loc[hyb, "已上线项目(电渠)"] = len(set(jf[(jf["行业部"] == hyb) & (jf["渠道"] == "电子")]["项目"]))
		df.loc[hyb, "昨日订单(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["外部下单日期"] == yesterday) & (jf["渠道"] == "电子")]["外部订单号"].count()
		df.loc[hyb, "本月总订单(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["下单月份"] == this_month) & (jf["渠道"] == "电子")]["外部订单号"].count()
		df.loc[hyb, "昨日产能(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["激活日期"] == yesterday) & (jf["渠道"] == "电子")]["外部订单号"].count()
		df.loc[hyb, "本月总产能(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["激活月份"] == this_month2) & (jf["渠道"] == "电子")]["外部订单号"].count()
		df.loc[hyb, "其中:中高端(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["激活月份"] == this_month2) & (jf["套餐名称"].str.contains("冰")) & (jf["渠道"] == "电子")]["外部订单号"].count()
		# 任务日均310
	# print(jf.loc[jf["套餐名称"].str.contains("冰")])

	assignment = 310
	days = int(yesterday[-2:])
	df["本月日均产能(整体)"] = df["本月总产能(整体)"] / days
	df["本月日均产能(电渠)"] = df["本月总产能(电渠)"] / days
	df["本月电渠占比"] = (df["本月总产能(电渠)"] / df["本月总产能(整体)"]).apply(lambda x: format(x, ".2%"))
	df["时序进度"] = (df["本月总产能(电渠)"] / (assignment * days)).apply(lambda x: format(x, ".2%"))

	return df

def run_jf():
	key_img = {}  # key_img对应关系
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("DELETE FROM key_img;") # 删除所有key_img内容，以便重新插入
		for xm in xm_set:
			dts = DrawTableSave(key=xm, title="%s订单情况" % xm, df=get_table(head="项目", key=xm))
			dts.init_color()
			dts.init_plt()
			result = dts.draw_and_save()
			key_img.update(result)
			logger.debug("%s已绘制成功" % xm)
		for hyb in hyb_set:
			dts = DrawTableSave(key=hyb, title="%s行业部订单情况" % hyb, df=get_table(head="行业部", key=hyb))
			dts.init_color()
			dts.init_plt()
			result = dts.draw_and_save()
			key_img.update(result)
			logger.debug("%s已绘制成功" % hyb)
		dts = DrawTableSave(key="行业部达产通报", title="行业部达产通报", df=get_hyb_total(), size_inches=(20.0 / 1.5, 10.0 / 1.5))
		dts.set_title_x(0.05)
		dts.init_color()
		dts.init_plt()
		result = dts.draw_and_save()
		key_img.update(result)
		logger.debug("%s已绘制成功" % "行业部达产通报")
		for key, img in key_img.items():
			c.execute("INSERT INTO key_img VALUES (?, ?)", (to_md5(key), img))
	return key_img

if __name__ == "__main__":
	# dts = DrawTableSave(key="行业部达产通报", title="行业部达产通报", df=get_hyb_total(), size_inches=(20.0/1.5, 10.0/1.5))
	# dts.set_title_x(0.05)
	# dts.init_color()
	# dts.init_plt()
	# dts.draw_and_save()
	run_jf()
	# 返回项目和图片的对应关系