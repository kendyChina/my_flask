# coding: utf-8

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import sqlite3


file_path = r"./csv"
file_name = r"jf.csv"
file = os.path.join(file_path, file_name)
target_path = r"./img"

sns.set_style({"font.sans-serif": ["simhei", "Arial"]})

jingf = pd.read_csv(file, encoding="gbk")
# 获取外部下单日期
jingf["外部下单日期"] = jingf["外部下单时间"].map(lambda x: str(x)[:10])
jingf["激活日期"] = jingf["入网时间"].map(lambda x: str(x)[:10])
jingf["首次充值日期"] = jingf["首次充值时间"].map(lambda x: str(x)[:10])
jingf["首充≥50"] = jingf["首次充值金额"].map(lambda x: "是" if x >= 50 else None)

xm_set = set(jingf["项目"])
xm_img = []

def get_xm(xm):
	# 项目可以用groupby来划分
	sh = jingf[jingf["项目"] == xm]
	#
	# sh.to_csv(os.path.join(file_path, "test.csv"), index=False)
	#
	groupbyrq = sh.groupby("外部下单日期")
	xmtb = groupbyrq["外部订单号", "入网时间", "首充≥50"].count()
	xmtb.loc["汇总"] = xmtb.apply(lambda x: x.sum())

	xmtb["激活率"] = (xmtb["入网时间"] / xmtb["外部订单号"]).apply(lambda x: format(x, ".2%"))
	xmtb["充值率"] = (xmtb["首充≥50"] / xmtb["入网时间"]).apply(lambda x: format(x, ".2%"))
	xmtb["综转率"] = (xmtb["首充≥50"] / xmtb["外部订单号"]).apply(lambda x: format(x, ".2%"))

	xmtb.rename(columns={"外部订单号": "订单量", "入网时间": "激活量"}, inplace=True)
	xmtb.style.bar(subset=["激活率", "充值率", "综转率"], color="#d65f5f", width=100)

	# 设置table
	rowcolor = []
	for i in range(len(xmtb.index)):
		if i % 2 == 0:
		    rowcolor.append("#DCDCDC")
		else:
		    rowcolor.append("white")

	cellcolor = []
	for i in range(len(xmtb.index)):
		if i % 2 == 0:
		    color = "#DCDCDC"
		else:
		    color = "white"
		temp = []
		for j in range(len(xmtb.columns)):
		    temp.append(color)
		cellcolor.append(temp)

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
	# 关闭坐标轴
	plt.axis("off")

	# 设置标题
	plt.title("%s订单情况" % xm)
	# 保存为jpg
	target = os.path.join(target_path, "%s.jpg" % xm)
	plt.savefig(target, dpi=150)
	plt.close()
	xm_img.append(target)
	with sqlite3.connect("db.db") as conn:
		c = conn.cursor()
		c.execute("INSERT INTO xm_img VALUES (?, ?);", (xm, target))


def run_jf():
	with sqlite3.connect("db.db") as conn:
		c = conn.cursor()
		c.execute("DELETE FROM xm_img;")
	for xm in xm_set:
		get_xm(xm)
	return dict(zip(xm_set, xm_img))

if __name__ == "__main__":
	run_jf()
	# 返回项目和图片的对应关系
