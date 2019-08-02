# coding: utf-8

import os, time, datetime
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3

mx_file = r"csv/jf.csv" # 明细路径
target_path = r"img" # 输出目标文件夹

sns.set_style({"font.sans-serif": ["simhei", "Arial"]}) # 设置字体风格

db = "db.db" # 数据库名称

jf = pd.read_csv(mx_file, encoding="gbk") # 读取csv文件

jf["外部下单日期"] = jf["外部下单时间"].map(lambda x: str(x)[:10]) # 获取外部下单日期，前十位
jf["激活日期"] = jf["入网时间"].map(lambda x: str(x)[:10]) # 获取激活日期，前十位
jf["首次充值日期"] = jf["首次充值时间"].map(lambda x: str(x)[:10]) # 获取首充日期，前十位
jf["首充≥50"] = jf["首次充值金额"].map(lambda x: "是" if x >= 50 else None) # 判断首充≥50
jf["激活月份"] = jf["激活月份"].map(lambda x: str(x)[:6])
jf["充值月份"] = jf["充值月份"].map(lambda x: str(x)[:6])

xm_set = set(jf["项目"]) # 项目set
hyb_set = set(jf["行业部"]) # 行业部set
key_img = {}

def draw_jpg(key, title, df):

	# 隔行设置row颜色：灰白相间
	rowcolor = []
	for i in range(len(df.index)):
		if i % 2 == 0:
			rowcolor.append("#DCDCDC") # 浅灰
		else:
			rowcolor.append("white")

	# 隔行设置cell颜色：灰白相间
	cellcolor = []
	for i in range(len(df.index)):
		if i % 2 == 0:
			color = "#DCDCDC" # 浅灰
		else:
			color = "white"
		cellcolor.append([color for x in range(len(df.columns))])

	# 设置表格样式
	plt.table(
		cellText=df.values,
		colLabels=df.columns,
		colWidths=[0.15]*len(df.columns),
		rowLabels=df.index,
		loc="best",
		cellLoc="center",
		colLoc="center",
		rowLoc="center",
		rowColours=rowcolor,
		cellColours=cellcolor
	)

	# 关闭坐标轴
	plt.xticks([])
	plt.yticks([])

	plt.axis("off")

	plt.title(
		"%s订单情况(%s日)" % (title, time.strftime("%m-%d", time.localtime(time.time()))),
		fontsize=18,
		verticalalignment="center",
		# horizontalalignment="left",
		fontweight="black",
		color="#000000",
		x=0.35
	) # 设置标题

	plt.gcf().set_size_inches(10.0/1.5, 15.0/1.5)
	target = os.path.join(target_path, r"%s.jpg" % key) # 保存为jpg
	plt.savefig(target, bbox_inches="tight", pad_inches=0.5)
	plt.close()

	key_img[key] = target

# 获取本月的index
# 及上个月的年月，首日
def get_two_month_dates():
	# 获取本月的年月
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

def get_img(head, key):

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

def run_jf():
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("DELETE FROM key_img;") # 删除所有key_img内容，以便重新插入
		for xm in xm_set:
			draw_jpg(key=xm, title=xm, df=get_img(head="项目", key=xm))
		for hyb in hyb_set:
			draw_jpg(key=hyb, title="%s行业部" % hyb, df=get_img(head="行业部", key=hyb))
		for key, img in key_img.items():
			c.execute("INSERT INTO key_img VALUES (?, ?)", (key, img))
	return key_img

if __name__ == "__main__":
	# test()
	run_jf()
	# 返回项目和图片的对应关系
