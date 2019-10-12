import sqlite3
from my_tools import Log

class InitDb(object):

    def __init__(self):
        self.db = "db.db"
        self.logger = Log(__name__).getlog()

    def run(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            try:
                # access_token
                c.execute("""
                    CREATE TABLE access_token
                    (token text not null,
                    time text not null);
                """)
                # key_img
                c.execute("""
                    CREATE TABLE key_img
                    (key text not null,
                    img text not null);
                """)
                # key_media
                c.execute("""
                    CREATE TABLE key_media
                    (key text not null,
                    media_id text not null); 
                """)
            except Exception as e:
                self.logger.exception(e)
            else:
                self.logger.info("{}、{}、{}初始化成功！".format("access_token", "key_img", "key_media"))

if __name__ == '__main__':
    InitDb().run()