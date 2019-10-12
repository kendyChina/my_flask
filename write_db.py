import sqlite3, os
from my_tools import to_md5, Log

class WriteImgIntoDb(object):

    def __init__(self):
        # 数据库名称
        self.db = "db.db"
        # img文件夹
        self.img_path = "img"
        # logger
        self.logger = Log(__name__).getlog()

    def run(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            # 删除所有key_img内容，以便重新插入
            c.execute("DELETE FROM key_img;")
            if os.path.isdir(self.img_path):
                for root, dirs, files in os.walk(self.img_path):
                    for file in files:
                        img = os.path.join(root, file)
                        (xm, extension) = os.path.splitext(file)
                        c.execute("INSERT INTO key_img VALUES (?, ?)", (to_md5(xm), img))

if __name__ == "__main__":
    WriteImgIntoDb().run()