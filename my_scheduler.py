# coding: utf-8

import schedule, datetime, requests, hashlib, os
from my_flask.my_tools import SSHConnection, get_ssh_passwd, get_logger

temp_file = r"csv/jf.csv"
remote_file = r"$HOME/my_flask/csv/jf.csv"

logger = get_logger()

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
        logger.info("经分网址返回码非200：%s" % resp.content)
        return False
    logger.debug("经分明细获取成功！")
    if os.path.exists(temp_file) is True:
        with open(temp_file, "rb") as f:
            md5_temp = hashlib.md5(f.read())
        md5_resp = hashlib.md5(resp.content)
        if md5_temp.digest() == md5_resp.digest():
            logger.debug("经分明细尚未更新！")
            return False
    with open(temp_file, "wb") as f:
        f.write(resp.content)
    logger.info("经分明细更新成功！")
    return True

def run_remote():
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
        "passwd": get_ssh_passwd()
    }
    chdir = "cd %s;" % os.path.join("/home/code/", os.path.dirname(__file__).split("/")[-1])
    export_pypath = "export PYTHONPATH=$PYTHONPATH:/home/code;"
    ssh = SSHConnection(host_dict)
    ssh.connect()
    logger.info("开始上传经分明细...")
    starttime = datetime.datetime.now()
    ssh.upload(temp_file, remote_file)
    endtime = datetime.datetime.now()
    logger.info("经分明细上传成功！耗时[%s]" % endtime-starttime)
    for py_file in ["jf.py", "upload_tmp_img.py"]:
        logger.info("开始运行%s..." % py_file)
        try:
            starttime = datetime.datetime.now()
            resp = ssh.run_cmd(chdir + export_pypath + "python %s" % py_file)
            endtime = datetime.datetime.now()
            logger.debug(resp)
            logger.info("%s运行成功！耗时[%s]" % (py_file, endtime-starttime))
        except Exception as e:
            logger.exception(e)
    ssh.close()

def run():
    if get_jf() == False:
        logger.debug("十分钟后重试...")
    else:
        run_remote()

def test():
    print("test!")

if __name__ == "__main__":
    logger.debug("开始执行schedule...")
    run()
    # schedule是先计时后执行，因此先执行一遍
    schedule.every(10).minutes.do(run)

    while True:
        schedule.run_pending()