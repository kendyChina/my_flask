# coding: utf-8

import time, datetime, os
import pandas as pd
import seaborn as sns
from my_flask.my_tools import Log
import xlsxwriter
import xlwings as xw
from PIL import ImageGrab

# 明细路径
jf_file = r"csv/jf.csv"
# 输出目标文件夹
img_path = "img"
# 设置字体风格
sns.set_style({"font.sans-serif": ["simhei", "Arial"]})
# 数据库名称
db = "db.db"
# 读取csv文件
jf = pd.read_csv(jf_file, encoding="gbk")
# 初始化logger
logger = Log(__name__).getlog()
# 临时excel用于截图
tmp_xlsx = "tmp.xlsx"

# 增加辅助字段
jf["外部下单日期"] = jf["外部下单时间"].map(lambda x: str(x)[:10])  # 获取外部下单日期，前十位
jf["激活日期"] = jf["入网时间"].map(lambda x: str(x)[:10])  # 获取激活日期，前十位
jf["首次充值日期"] = jf["首次充值时间"].map(lambda x: str(x)[:10])  # 获取首充日期，前十位
jf["首充≥50"] = jf["首次充值金额"].map(lambda x: "是" if x >= 50 else None)  # 判断首充≥50
jf["激活月份"] = jf["激活月份"].map(lambda x: str(x)[:6])
jf["充值月份"] = jf["充值月份"].map(lambda x: str(x)[:6])

hyb_set = set(jf["行业部"])  # 行业部set

this_month = datetime.datetime.now().month
this_day = datetime.datetime.now().day

def xlsx_to_img(img_name):

    app = xw.App(visible=False, add_book=False)
    # 打开文件
    wb = app.books.open(tmp_xlsx)
    sheet = wb.sheets[0]
    # 获取有内容的range
    all = sheet.used_range
    # 复制图片区域
    all.api.CopyPicture()
    # 黏贴
    sheet.api.Paste()

    # 当前图片
    pic = sheet.pictures[0]
    # 复制图片
    pic.api.Copy()

    # 获取剪贴板的图片数据
    img = ImageGrab.grabclipboard()
    img.save(img_name)

    pic.delete()
    wb.close()
    app.quit()

def get_two_month_dates():
    """
    :return:
    this_dates: 本月至今2019-09-09
    prev_year_month: 201909
    prev_first_day: 2019-09
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
    prev_year_month = prev_year + prev_month  # yyyymm
    prev_first_day = prev_year + "-" + prev_month  # yyyy-mm

    # 获取本月的日期索引
    this_dates = pd.date_range(start=this_first_day, end=this_today).strftime("%Y-%m-%d")

    return (this_dates, prev_year_month, prev_first_day)

class DrawXm(object):

    def __init__(self, jf):
        self.xm_set = set(jf["项目"])

    def get_df(self, xm):
        # 明细
        mx = jf[jf["项目"] == xm]

        this_dates, prev_year_month, prev_first_day = get_two_month_dates()
        # 标题
        colunms = ["订单量", "激活量", "激活率", "首充≥50", "充值率", "综转率", "当日激活", "当日产能"]
        # 纵坐标索引
        index = "%s月汇总" % prev_first_day[-2:]
        # 上月df
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
        this_df.loc["%s月汇总" % this_month] = this_df.apply(lambda x: x.sum())
        try:
            this_df["激活率"] = (this_df["激活量"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
            this_df["充值率"] = (this_df["首充≥50"] / this_df["激活量"]).apply(lambda x: format(x, ".2%"))
            this_df["综转率"] = (this_df["首充≥50"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
        except:
            this_df["激活率"] = format(0, ".2%")
            this_df["充值率"] = format(0, ".2%")
            this_df["综转率"] = format(0, ".2%")

        return prev_df.append(this_df)

    def run(self):
        """
        按照项目画出所有的通报
        :return:
        """
        for xm in self.xm_set:
            df = self.get_df(xm)

            with xlsxwriter.Workbook(tmp_xlsx) as wb:
                ws = wb.add_worksheet()
                ws.set_column("B:G", width=7)
                ws.set_column("A:A", width=12)
                ws.set_column("E:E", width=9)
                ws.set_column("H:I", width=10)

                title_format = wb.add_format(
                    {"align": "center", "valign": "vcenter", "bold": True, "border": True, "font_name": "等线"}
                )
                ws.merge_range("A1:I1", "%s项目订单情况-%s月%s日" % (xm, this_month, this_day), title_format)
                head_format = wb.add_format(
                    {"align": "center", "valign": "vcenter", "bold": True, "bg_color": "#C00000", "font_color": "white",
                     "border": True, "font_name": "等线"}
                )
                center_format = wb.add_format(
                    {"align": "center", "valign": "vcenter", "border": True, "font_name": "等线"})
                ws.write(1, 0, "日期", head_format)
                i = 1
                for col in df.columns:
                    ws.write(1, i, col, head_format)
                    i += 1
                i = 2
                for index in df.index:
                    ws.write(i, 0, index, center_format)
                    j = 1
                    for col in df.columns:
                        ws.write(i, j, df.loc[index, col], center_format)
                        j += 1
                    i += 1
            logger.debug("开始画{}".format(xm))
            xlsx_to_img(os.path.join(img_path, "{}.png".format(xm)))
            logger.debug("结束")

class DrawHyb(object):

    def __init__(self, jf):
        self.hyb_set = set(jf["行业部"])

    def get_df(self, hyb):
        # 明细
        mx = jf[jf["行业部"] == hyb]

        this_dates, prev_year_month, prev_first_day = get_two_month_dates()
        # 标题
        colunms = ["订单量", "激活量", "激活率", "首充≥50", "充值率", "综转率", "当日激活", "当日产能"]
        # 纵坐标索引
        index = "%s月汇总" % prev_first_day[-2:]
        # 上月df
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
        this_df.loc["%s月汇总" % this_month] = this_df.apply(lambda x: x.sum())
        try:
            this_df["激活率"] = (this_df["激活量"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
            this_df["充值率"] = (this_df["首充≥50"] / this_df["激活量"]).apply(lambda x: format(x, ".2%"))
            this_df["综转率"] = (this_df["首充≥50"] / this_df["订单量"]).apply(lambda x: format(x, ".2%"))
        except:
            this_df["激活率"] = format(0, ".2%")
            this_df["充值率"] = format(0, ".2%")
            this_df["综转率"] = format(0, ".2%")

        return prev_df.append(this_df)

    def run(self):
        """
        按照项目画出所有的通报
        :return:
        """
        for hyb in self.hyb_set:
            df = self.get_df(hyb)

            with xlsxwriter.Workbook(tmp_xlsx) as wb:
                ws = wb.add_worksheet()
                ws.set_column("B:G", width=7)
                ws.set_column("A:A", width=12)
                ws.set_column("E:E", width=9)
                ws.set_column("H:I", width=10)

                title_format = wb.add_format(
                    {"align": "center", "valign": "vcenter", "bold": True, "border": True, "font_name": "等线"}
                )
                ws.merge_range("A1:I1", "%s行业部订单情况-%s月%s日" % (hyb, this_month, this_day), title_format)
                head_format = wb.add_format(
                    {"align": "center", "valign": "vcenter", "bold": True, "bg_color": "#C00000", "font_color": "white",
                     "border": True, "font_name": "等线"}
                )
                center_format = wb.add_format(
                    {"align": "center", "valign": "vcenter", "border": True, "font_name": "等线"})
                ws.write(1, 0, "日期", head_format)
                i = 1
                for col in df.columns:
                    ws.write(1, i, col, head_format)
                    i += 1
                i = 2
                for index in df.index:
                    ws.write(i, 0, index, center_format)
                    j = 1
                    for col in df.columns:
                        ws.write(i, j, df.loc[index, col], center_format)
                        j += 1
                    i += 1
            logger.debug("开始画{}".format(hyb))
            xlsx_to_img(os.path.join(img_path, "{}.png".format(hyb)))
            logger.debug("结束")

def get_hyb_total():
    """
	获取行业部整体通报
	:return:
	"""
    columns = ["已上线项目(电渠)", "昨日订单(电渠)", "本月总订单(电渠)", "昨日产能(电渠)", "本月总产能(电渠)", "本月日均产能(电渠)", "其中:中高端(电渠)", "本月电渠占比",
               "时序进度",
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
        df.loc[hyb, "昨日订单(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["外部下单日期"] == yesterday) & (jf["渠道"] == "电子")][
            "外部订单号"].count()
        df.loc[hyb, "本月总订单(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["下单月份"] == this_month) & (jf["渠道"] == "电子")][
            "外部订单号"].count()
        df.loc[hyb, "昨日产能(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["激活日期"] == yesterday) & (jf["渠道"] == "电子")][
            "外部订单号"].count()
        df.loc[hyb, "本月总产能(电渠)"] = jf[(jf["行业部"] == hyb) & (jf["激活月份"] == this_month2) & (jf["渠道"] == "电子")][
            "外部订单号"].count()
        df.loc[hyb, "其中:中高端(电渠)"] = \
        jf[(jf["行业部"] == hyb) & (jf["激活月份"] == this_month2) & (jf["套餐名称"].str.contains("冰")) & (jf["渠道"] == "电子")][
            "外部订单号"].count()
    # 任务日均310
    # print(jf.loc[jf["套餐名称"].str.contains("冰")])

    assignment = 310
    days = int(yesterday[-2:])
    df["本月日均产能(整体)"] = df["本月总产能(整体)"] / days
    df["本月日均产能(电渠)"] = df["本月总产能(电渠)"] / days
    df["本月电渠占比"] = (df["本月总产能(电渠)"] / df["本月总产能(整体)"]).apply(lambda x: format(x, ".2%"))
    df["时序进度"] = (df["本月总产能(电渠)"] / (assignment * days)).apply(lambda x: format(x, ".2%"))

    return df

def get_qfqx():
    """
	获取区分区销报表
	:return:
	"""
    qf_list = ["白云集客", "天河集客", "番禺集客", "花都集客", "海珠集客", "增城集客", "黄埔集客", "荔湾集客", "越秀集客", "南沙集客", "从化集客", "大学城", "战客"]
    qx_list = ["白云南销售", "白云北销售", "天河销售", "番禺销售", "花都销售", "海珠销售", "增城销售", "黄埔销售", "荔湾销售", "越秀销售", "南沙销售", "从化销售"]
    # today = datetime.datetime.now().strftime("%Y-%m-%d")
    # yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    today = "2019-09-02"
    yesterday = "2019-09-01"
    month = "2019-09"
    month2 = "201909"
    colunms = ["%s日新增订单" % yesterday[-2:], "本月累计订单", "%s日新增产能" % yesterday[-2:], "本月累计产能"]
    qf_df = pd.DataFrame(data=None, index=qf_list, columns=colunms)
    for qf in qf_list:
        mx = jf[jf["营销单元"] == qf]
        qf_df.loc[qf, colunms[0]] = mx[mx["外部下单日期"] == yesterday]["外部订单号"].count()
        qf_df.loc[qf, colunms[1]] = mx[mx["下单月份"] == month]["外部订单号"].count()
        qf_df.loc[qf, colunms[2]] = mx[mx["首次充值日期"] == yesterday]["首充≥50"].count()
        qf_df.loc[qf, colunms[3]] = mx[mx["充值月份"] == month2]["首充≥50"].count()
    qf_df.loc["区分合计"] = qf_df.apply(lambda x: x.sum())

    qx_df = pd.DataFrame(data=None, index=qx_list, columns=colunms)
    for qx in qx_list:
        mx = jf[jf["营销单元"] == qx]
        qx_df.loc[qx, colunms[0]] = mx[mx["外部下单日期"] == yesterday]["外部订单号"].count()
        qx_df.loc[qx, colunms[1]] = mx[mx["下单月份"] == month]["外部订单号"].count()
        qx_df.loc[qx, colunms[2]] = mx[mx["首次充值日期"] == yesterday]["首充≥50"].count()
        qx_df.loc[qx, colunms[3]] = mx[mx["充值月份"] == month2]["首充≥50"].count()
    qx_df.loc["区销合计"] = qx_df.apply(lambda x: x.sum())

    df = qf_df.append(qx_df)

    mx = jf[jf["营销单元"] == "本部"]
    df.loc["市本部", colunms[0]] = mx[mx["外部下单日期"] == yesterday]["外部订单号"].count()
    df.loc["市本部", colunms[1]] = mx[mx["下单月份"] == month]["外部订单号"].count()
    df.loc["市本部", colunms[2]] = mx[mx["首次充值日期"] == yesterday]["首充≥50"].count()
    df.loc["市本部", colunms[3]] = mx[mx["充值月份"] == month2]["首充≥50"].count()

    df.loc["全司合计", colunms[0]] = jf[jf["外部下单日期"] == yesterday]["外部订单号"].count()
    df.loc["全司合计", colunms[1]] = jf[jf["下单月份"] == month]["外部订单号"].count()
    df.loc["全司合计", colunms[2]] = jf[jf["首次充值日期"] == yesterday]["首充≥50"].count()
    df.loc["全司合计", colunms[3]] = jf[jf["充值月份"] == month2]["首充≥50"].count()

    with xlsxwriter.Workbook("test.xlsx") as wb:
        ws = wb.add_worksheet()
        ws.set_column("A:F", width=11)

        title_format = wb.add_format(
            {"align": "center", "valign": "vcenter", "bold": True, "border": True, "font_name": "等线"})
        ws.merge_range("A1:F1", "本地引流项目推进通报-9月2日", title_format)

        head_format = wb.add_format(
            {"align": "center", "valign": "vcenter", "bold": True, "bg_color": "#C00000", "font_color": "white",
             "border": True, "font_name": "等线"})
        ws.merge_range("A2:A3", "区县", head_format)
        ws.merge_range("B2:B3", "营销单元", head_format)
        ws.merge_range("C2:D2", "订单", head_format)
        ws.write("C3", "1日新增", head_format)
        ws.write("D3", "本月累计", head_format)
        ws.merge_range("E2:F2", "产能", head_format)
        ws.write("E3", "1日新增", head_format)
        ws.write("F3", "本月累计", head_format)

        center_format = wb.add_format({"align": "center", "valign": "vcenter", "border": True, "font_name": "等线"})
        center_bold_format = wb.add_format({"align": "center", "valign": "vcenter", "border": True, "font_name": "等线", "bold": True})
        ws.merge_range("A4:A16", "区分公司", center_format)

        i = 4
        for qf in qf_list:
            qf_ = qf.replace("集客", "")
            ws.write("B%s" % i, qf_, center_format)
            ws.write("C%s" % i, df.loc[qf, colunms[0]], center_format)
            ws.write("D%s" % i, df.loc[qf, colunms[1]], center_format)
            ws.write("E%s" % i, df.loc[qf, colunms[2]], center_format)
            ws.write("F%s" % i, df.loc[qf, colunms[3]], center_format)
            i += 1

        ws.merge_range("A17:B17", "区分合计", center_bold_format)
        ws.write("C%s" % 17, df.loc["区分合计", colunms[0]], center_bold_format)
        ws.write("D%s" % 17, df.loc["区分合计", colunms[1]], center_bold_format)
        ws.write("E%s" % 17, df.loc["区分合计", colunms[2]], center_bold_format)
        ws.write("F%s" % 17, df.loc["区分合计", colunms[3]], center_bold_format)

        ws.merge_range("A18:A29", "区分公司", center_format)

        i = 18
        for qx in qx_list:
            qx_ = qx.replace("销售", "")
            ws.write("B%s" % i, qx_, center_format)
            ws.write("C%s" % i, df.loc[qx, colunms[0]], center_format)
            ws.write("D%s" % i, df.loc[qx, colunms[1]], center_format)
            ws.write("E%s" % i, df.loc[qx, colunms[2]], center_format)
            ws.write("F%s" % i, df.loc[qx, colunms[3]], center_format)
            i += 1

        ws.merge_range("A30:B30", "区销合计", center_bold_format)
        ws.write("C%s" % 30, df.loc["区销合计", colunms[0]], center_bold_format)
        ws.write("D%s" % 30, df.loc["区销合计", colunms[1]], center_bold_format)
        ws.write("E%s" % 30, df.loc["区销合计", colunms[2]], center_bold_format)
        ws.write("F%s" % 30, df.loc["区销合计", colunms[3]], center_bold_format)

        ws.merge_range("A31:B31", "市本部", center_bold_format)
        ws.write("C%s" % 31, df.loc["市本部", colunms[0]], center_bold_format)
        ws.write("D%s" % 31, df.loc["市本部", colunms[1]], center_bold_format)
        ws.write("E%s" % 31, df.loc["市本部", colunms[2]], center_bold_format)
        ws.write("F%s" % 31, df.loc["市本部", colunms[3]], center_bold_format)

        ws.merge_range("A32:B32", "全司合计", center_bold_format)
        ws.write("C%s" % 32, df.loc["全司合计", colunms[0]], center_bold_format)
        ws.write("D%s" % 32, df.loc["全司合计", colunms[1]], center_bold_format)
        ws.write("E%s" % 32, df.loc["全司合计", colunms[2]], center_bold_format)
        ws.write("F%s" % 32, df.loc["全司合计", colunms[3]], center_bold_format)

        app = xw.App(visible=False, add_book=False)
        # 打开文件
        wb = app.books.open("test.xlsx")
        sheet = wb.sheets[0]
        # 获取有内容的range
        all = sheet.used_range
        # 复制图片区域
        all.api.CopyPicture()
        # 黏贴
        sheet.api.Paste()

        # 当前图片
        pic = sheet.pictures[0]
        # 复制图片
        pic.api.Copy()

        # 获取剪贴板的图片数据
        img = ImageGrab.grabclipboard()
        img_name = "test.png"
        img.save(img_name)

        pic.delete()
        wb.close()
        app.quit()

def run_jf():
    logger.info("开始移除img文件夹的所有文件")
    if os.path.isdir(img_path):
        for root, dirs, files in os.walk(img_path):
            for file in files:
                os.remove(os.path.join(root, file))
    logger.info("移除完毕！")
    DrawXm(jf).run()
    logger.info("项目绘制完成！")
    DrawHyb(jf).run()
    logger.info("行业部绘制完成！")

# def run_jf():
#     # key_img对应关系
#     key_img = {}
#     with sqlite3.connect(db) as conn:
#         c = conn.cursor()
#         # 删除所有key_img内容，以便重新插入
#         c.execute("DELETE FROM key_img;")
#         for xm in xm_set:
#             dts = DrawTableSave(key=xm, title="%s订单情况" % xm, df=get_table(head="项目", key=xm))
#             dts.init_color()
#             dts.init_plt()
#             result = dts.draw_and_save()
#             key_img.update(result)
#             logger.debug("%s已绘制成功" % xm)
#         for hyb in hyb_set:
#             dts = DrawTableSave(key=hyb, title="%s行业部订单情况" % hyb, df=get_table(head="行业部", key=hyb))
#             dts.init_color()
#             dts.init_plt()
#             result = dts.draw_and_save()
#             key_img.update(result)
#             logger.debug("%s已绘制成功" % hyb)
#         dts = DrawTableSave(key="行业部达产通报", title="行业部达产通报", df=get_hyb_total(), size_inches=(20.0 / 1.5, 10.0 / 1.5))
#         dts.set_title_x(0.05)
#         dts.init_color()
#         dts.init_plt()
#         result = dts.draw_and_save()
#         key_img.update(result)
#         logger.debug("%s已绘制成功" % "行业部达产通报")
#         for key, img in key_img.items():
#             c.execute("INSERT INTO key_img VALUES (?, ?)", (to_md5(key), img))
#     return key_img


if __name__ == "__main__":
    run_jf()
