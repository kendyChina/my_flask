# coding: utf-8

import schedule, datetime, requests, hashlib, os
from my_flask.my_tools import SSHConnection, get_ssh_passwd, Log
from my_flask.jf import run_jf

jf_file = r"csv/jf.csv"

logger = Log(__name__).getlog()

def get_jf():
    """
    1）读取经分明细
    2）判断更新情况
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
    if os.path.exists(jf_file) is True:
        with open(jf_file, "rb") as f:
            md5_temp = hashlib.md5(f.read())
        md5_resp = hashlib.md5(resp.content)
        if md5_temp.digest() == md5_resp.digest():
            logger.debug("经分明细尚未更新！")
            return False
    with open(jf_file, "wb") as f:
        f.write(resp.content)
    logger.info("经分明细更新成功！")
    return True

def upload_and_run():
    """
    上传经分明细
    运行远端jf.py
    运行远端upload_tmp_img.py
    :return:
    """

    # 本地img文件夹
    img_path = "img"
    # 远端img文件夹
    remote_img_path = r"/home/kendy/my_flask/img"

    host_dict = {
        "host": "101.37.77.27",
        "port": 22,
        "username": "kendy",
        "passwd": get_ssh_passwd()
    }

    ssh = SSHConnection(host_dict)
    ssh.connect()
    logger.info("开始上传通报...")
    starttime = datetime.datetime.now()
    if os.path.isdir(img_path):
        for root, dirs, files in os.walk(img_path):
            for file in files:
                img = os.path.join(root, file)
                remote_img = os.path.join(remote_img_path, file)
                ssh.upload(img, remote_img)
                logger.debug("{}上传成功！".format(file))
    endtime = datetime.datetime.now()
    logger.info("通报上传成功！耗时[%s]" % (endtime - starttime, ))

    workon = "workon my_flask;"
    chdir = "cd /home/kendy/my_flask;"
    export_pypath = "export PYTHONPATH=$PYTHONPATH:$HOME;"

    logger.info("开始写入数据库")
    try:
        starttime = datetime.datetime.now()
        resp = ssh.run_cmd(workon + chdir + export_pypath + "python {}".format("write_db.py"))
        logger.debug(resp)
        endtime = datetime.datetime.now()
        logger.info("写入成功，耗时{}".format(endtime - starttime))
    except Exception as e:
        logger.exception(e)
    # for py_file in ["jf.py", "upload_tmp_img.py"]:
    #     logger.info("开始运行%s..." % py_file)
    #     try:
    #         starttime = datetime.datetime.now()
    #         resp = ssh.run_cmd(workon + chdir + export_pypath + "python %s" % py_file)
    #         endtime = datetime.datetime.now()
    #         logger.debug(resp)
    #         logger.info("%s运行成功！耗时[%s]" % (py_file, endtime-starttime))
    #     except Exception as e:
    #         logger.exception(e)
    ssh.close()

def run():
    if get_jf() == False:
        logger.debug("十分钟后重试...")
    else:
        run_jf()
        upload_and_run()
        # run_remote()

if __name__ == "__main__":
    # logger.debug("开始执行schedule...")
    # run()
    #
    # schedule.every(10).minutes.do(run) # schedule是先计时后执行，因此先执行一遍
    #
    # while True:
    #     schedule.run_pending()
    # get_jf()
    run_jf()