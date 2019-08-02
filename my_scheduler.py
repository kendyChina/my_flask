# coding: utf-8

import schedule, time, datetime, requests, ftplib, hashlib, os, logging
from my_flask import SSHConnection

temp_file = r"csv_temp/jf.csv"
remote_file = r"/home/code/my_flask/csv/jf.csv"

# 配置logger
logger = logging.getLogger("logger")

handler1 = logging.StreamHandler()
handler2 = logging.FileHandler(filename="log/scheduler.log", encoding="utf-8", mode="a+")

logger.setLevel(logging.DEBUG)
handler1.setLevel(logging.DEBUG)
handler2.setLevel(logging.WARNING)

formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
handler1.setFormatter(formatter)
handler2.setFormatter(formatter)

logger.addHandler(handler1)
logger.addHandler(handler2)

def get_ftp_passwd():
    ftp_passwd_file = "passwd/ftp_passwd.txt"
    if os.path.exists(ftp_passwd_file):
        with open(ftp_passwd_file) as f:
            ftp_passwd = f.readline().strip()
            logger.info("获取ftp密码成功！")
    else:
        ftp_passwd = input("请输入ftp密码：")
    return ftp_passwd

def get_jf():
    """
    读取经分明细
    判断更新情况
    若已更新则替换，并返回True
    反之则返回False
    :return:
    """
    url = r"http://kingcard.gz.gd.unicom.local/static/document/jingfen_detail.csv"
    resp = requests.get(url)
    if resp.status_code != 200:
        logger.warning("经分网址返回码非200：%s" % resp.content)
        return False
    if os.path.exists(temp_file) is True:
        with open(temp_file, "rb") as f:
            md5_temp = hashlib.md5(f.read())
        md5_resp = hashlib.md5(resp.content)
        if md5_temp.digest() == md5_resp.digest():
            logger.info("经分明细尚未更新！")
            return False
    with open(temp_file, "wb") as f:
        f.write(resp.content)
    logger.warning("经分明细更新成功！")
    return True

def proc_remote():
    """
    上传经分明细
    运行远端jf.py
    运行远端upload_tmp_img.py
    :return:
    """
    host_dict = {
        "host": "139.155.117.186",
        "port": 22,
        "username": "kendy",
        "passwd": get_ftp_passwd()
    }
    chdir = "cd %s;" % os.path.join("/home/code/", os.path.dirname(__file__).split("/")[-1])
    export_pypath = "export PYTHONPATH=$PYTHONPATH:/home/code;"
    ssh = SSHConnection.SSHConnection(host_dict)
    ssh.connect()
    logger.warning("开始上传经分明细...")
    ssh.upload(temp_file, remote_file)
    logger.warning("经分明细上传成功！")
    for py_file in ["jf.py", "upload_tmp_img.py"]:
        logger.warning("开始运行%s..." % py_file)
        try:
            resp = ssh.run_cmd(chdir + export_pypath + "python %s" % py_file)
            logger.info(resp)
            logger.warning("%s运行成功！" % py_file)
        except Exception as e:
            logger.exception(e)

    ssh.close()

def run():
    while get_jf() == False:
        logger.info("十分钟后重试...")
        time.sleep(600) # 十分钟
    proc_remote()


if __name__ == "__main__":
    schedule.every().day.at("06:00").do(run)

    while True:
        schedule.run_pending()
