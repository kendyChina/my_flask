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

formatter = logging.Formatter("%(asctime)s %(name)s:%(levelname)s:%(message)s")
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
    url = r"http://kingcard.gz.gd.unicom.local/static/document/jingfen_detail.csv"
    resp = requests.get(url)
    if resp.status_code != 200:
        logger.warning("经分网址返回码非200：%s" % resp.content)
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

def upload_jf():
    host = "139.155.117.186"
    username = "kendy"
    ftp_passwd = get_ftp_passwd()
    with ftplib.FTP(host, user=username, passwd=ftp_passwd) as ftp:
        bufsize = 1024
        try:
            logger.info("开始上传ftp文件...")
            with open(temp_file, "rb") as f:
                ftp.storbinary("STOR %s" % remote_file, f, bufsize)
            logger.warning("上传ftp文件成功！")
        except Exception as e:
            logger.exception(e)

def run():
    while get_jf() == False:
        logger.info("十分钟后重试...")
        time.sleep(600) # 十分钟
    upload_jf()

def test():
    host_dict = {
        "host": "139.155.117.186",
        "port": 22,
        "username": "kendy",
        "passwd": get_ftp_passwd()
    }
    chdir = "cd %s;" % os.path.join("/home/code/", os.path.dirname(__file__).split("/")[-1])
    ssh = SSHConnection.SSHConnection(host_dict)
    ssh.connect()
    # logger.info("开始上传经分明细...")
    # ssh.upload(temp_file, remote_file)
    # logger.warning("经分明细上传成功！")
    logger.info("开始运行jf.py...")
    try:
        resp = ssh.run_cmd(chdir + "python jf.py")
        logger.info(resp)
        logger.warning("jf.py运行成功！")
    except Exception as e:
        logger.exception(e)
    logger.info("开始运行upload_tmp_img.py...")
    try:
        resp = ssh.run_cmd(chdir + "python upload_tmp_img.py")
        logger.info(resp)
        logger.warning("upload_tmp_img.py运行成功！")
    except Exception as e:
        logger.exception(e)
    ssh.close()

if __name__ == "__main__":
    # schedule.every().day.at("06:00").do(run)
    #
    # while True:
    #     schedule.run_pending()
    # get_jf()
    # upload_jf()
    test()
