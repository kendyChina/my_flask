# coding: utf-8

import os, time, datetime
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3

mx_path = r"./csv" # 明细存放目录
mx_name = r"jf.csv" # 明细文件名
mx_file = os.path.join(mx_path, mx_name) # 明细路径
target_path = r"./img" # 输出目标文件夹

sns.set_style({"font.sans-serif": ["simhei", "Arial"]}) # 设置字体风格

db = "db.db" # 数据库名称

jf = pd.read_csv(mx_file, encoding="gbk") # 读取csv文件

jf["外部下单日期"] = jf["外部下单时间"].map(lambda x: str(x)[:10]) # 获取外部下单日期，前十位
jf["激活日期"] = jf["入网时间"].map(lambda x: str(x)[:10]) # 获取激活日期，前十位
jf["首次充值日期"] = jf["首次充值时间"].map(lambda x: str(x)[:10]) # 获取首充日期，前十位
jf["首充≥50"] = jf["首次充值金额"].map(lambda x: "是" if x >= 50 else None) # 判断首充≥50

xm_set = set(jf["项目"])
xm_img = {}

def draw_jpg(xm, df):

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

	plt.title("%s订单情况(%s日)" % (xm, time.strftime("%m-%d", time.localtime(time.time())))) # 设置标题

	plt.gcf().set_size_inches(10.0/1.5, 15.0/1.5)
	target = os.path.join(target_path, r"%s.jpg" % xm) # 保存为jpg
	plt.savefig(target, bbox_inches="tight", pad_inches=0.5)
	plt.close()

	xm_img[xm] = target

def get_two_month_dates():
	# 获取本月的年月
	this_year = datetime.datetime.now().year
	this_month = datetime.datetime.now().month

	# 获取本月的第一天和今天
	this_first_day = datetime.date(this_year, this_month, 1)
	this_today = time.strftime("%Y-%m-%d", time.localtime())

	# 获取上月的最后一天
	prev_last_day = this_first_day - datetime.timedelta(days=1)

	# 通过上月的最后一天获取上月的天数
	prev_periods = prev_last_day.day

	# 获取近两个月的日期索引
	this_dates = pd.date_range(start=this_first_day, end=this_today).strftime("%Y-%m-%d")
	prev_dates = pd.date_range(end=prev_last_day, periods=prev_periods).strftime("%Y-%m-%d")

	return (this_dates, prev_dates)

def get_img(xm):

	xmmx = jf[jf["项目"] == xm] # 项目明细

	this_dates, prev_dates = get_two_month_dates()
	colunms = ["订单量", "激活量", "激活率", "首充≥50", "充值率", "综转率", "当日激活", "当日产能"]
	# prev_df = pd.DataFrame(data=None, index=prev_dates, columns=colunms)
	# for date in prev_dates:
	# 	date_df = xmmx["外部下单日期"] == date
	# 	prev_df.loc[date, "订单量"] = xmmx[date_df]["外部订单号"].count()
	# 	prev_df.loc[date, "激活量"] = xmmx[date_df]["入网时间"].count()
	# 	prev_df.loc[date, "首充≥50"] = xmmx[date_df]["首充≥50"].count()
	# 	prev_df.loc[date, "当日激活"] = xmmx[xmmx["激活日期"] == date]["激活日期"].count()
	# 	prev_df.loc[date, "当日产能"] = xmmx[xmmx["首次充值时间"] == date]["首充≥50"].count()
	# prev_df.loc["%s月汇总" % prev_dates[0][5:7]] = prev_df.apply(lambda x: x.sum())
	# prev_df = pd.DataFrame(data=prev_df.tail(1))
	# prev_df["激活率"] = (prev_df["激活量"] / prev_df["订单量"]).apply(lambda x: format(x, ".2%"))
	# prev_df["充值率"] = (prev_df["首充≥50"] / prev_df["激活量"]).apply(lambda x: format(x, ".2%"))
	# prev_df["综转率"] = (prev_df["首充≥50"] / prev_df["订单量"]).apply(lambda x: format(x, ".2%"))
	# print(prev_df)

	this_df = pd.DataFrame(data=None, index=this_dates, columns=colunms)
	for date in this_dates:
		date_df = xmmx["外部下单日期"] == date
		this_df.loc[date, "订单量"] = xmmx[date_df]["外部订单号"].count()
		this_df.loc[date, "激活量"] = xmmx[date_df]["入网时间"].count()
		this_df.loc[date, "首充≥50"] = xmmx[date_df]["首充≥50"].count()
		this_df.loc[date, "当日激活"] = xmmx[xmmx["激活日期"] == date]["激活日期"].count()
		this_df.loc[date, "当日产能"] = xmmx[xmmx["首次充值日期"] == date]["首充≥50"].count()
	this_df.loc["%s月汇总" % this_dates[0][5:7]] = this_df.apply(lambda x: x.sum())
	try:
		this_df["激活率"] = (this_df["激活量"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
		this_df["充值率"] = (this_df["首充≥50"] / this_df["激活量"]).apply(lambda x: format(x, ".2%"))
		this_df["综转率"] = (this_df["首充≥50"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
	except:
		this_df["激活率"] = format(0, ".2%")
		this_df["充值率"] = format(0, ".2%")
		this_df["综转率"] = format(0, ".2%")

	return this_df

def run_jf():
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("DELETE FROM xm_img;") # 删除所有xm_img内容，以便重新插入
		for xm in xm_set:
			draw_jpg(xm, get_img(xm))
		for xm, img in xm_img.items():
			c.execute("INSERT INTO xm_img VALUES (?, ?)", (xm, img))
	return xm_img

def test():
	xm_time = {}
	for xm in xm_set:
		starttime = time.time()
		draw_jpg(xm, get_img(xm))
		pay_time = time.strftime("%M-%S", time.localtime(time.time() - starttime))
		xm_time[xm] = pay_time
		print("%s: %s" % (xm, pay_time))

if __name__ == "__main__":
	# test()
	run_jf()
	# 返回项目和图片的对应关系
