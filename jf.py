# coding: utf-8

import os
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

# 绘制项目的转化表，并把{xm:img}对应关系作为xm_img返回
def get_img(xm):
	# 项目可以用groupby来划分
	xm = jf[jf["项目"] == xm]

	groupbyrq = xm.groupby("外部下单日期") # 以外部下单日期为group
	# xmtb = 项目通报
	xmtb = groupbyrq["外部订单号", "入网时间", "首充≥50"].count() # 计算订单量、激活量、首充量
	xmtb.loc["汇总"] = xmtb.apply(lambda x: x.sum()) # 增加汇总行，为订单量、激活量、首充量的总和

	# 计算几乎率、充值率、综转率，并以xx.xx%格式输出
	xmtb["激活率"] = (xmtb["入网时间"] / xmtb["外部订单号"]).apply(lambda x: format(x, ".2%"))
	xmtb["充值率"] = (xmtb["首充≥50"] / xmtb["入网时间"]).apply(lambda x: format(x, ".2%"))
	xmtb["综转率"] = (xmtb["首充≥50"] / xmtb["外部订单号"]).apply(lambda x: format(x, ".2%"))

	xmtb.rename(columns={"外部订单号": "订单量", "入网时间": "激活量"}, inplace=True) # 重命名表头
	# xmtb.style.bar(subset=["激活率", "充值率", "综转率"], color="#d65f5f", width=100)

	# 隔行设置row颜色：灰白相间
	rowcolor = []
	for i in range(len(xmtb.index)):
		if i % 2 == 0:
			rowcolor.append("#DCDCDC") # 浅灰
		else:
			rowcolor.append("white")

	# 隔行设置cell颜色：灰白相间
	cellcolor = []
	for i in range(len(xmtb.index)):
		if i % 2 == 0:
			color = "#DCDCDC" # 浅灰
		else:
			color = "white"
		# temp = []
		# for j in range(len(xmtb.columns)):
		# 	temp.append(color)
		# cellcolor.append(temp)
		cellcolor.append([color for x in range(len(xmtb.columns))])

	plt.table(
		cellText=xmtb.values,
		colLabels=xmtb.columns,
		colWidths=[0.13]*len(xmtb.columns),
		rowLabels=xmtb.index,
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

	plt.title("%s订单情况" % xm) # 设置标题

	target = os.path.join(target_path, "%s.jpg" % xm) # 保存为jpg
	plt.savefig(target, dpi=150)
	plt.close()

	xm_img[xm] = target

def run_jf(self):
	with sqlite3.connect(db) as conn:
		c = conn.cursor()
		c.execute("DELETE FROM xm_img;") # 删除所有xm_img内容，以便重新插入
		for xm in xm_set:
			get_img(xm)
		for xm, img in xm_img.items():
			c.execute("INSERT INTO xm_img VALUES (?, ?)", (xm, img))
	return xm_img

if __name__ == "__main__":
	run_jf()
	# 返回项目和图片的对应关系
