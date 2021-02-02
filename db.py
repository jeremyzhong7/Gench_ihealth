import pymysql
from Health_logger import logger

class db:
    def __init__(self):
        self.DBHOST = 'localhost'
        self.DBUSER = 'root'
        self.DBPASSWORD = '123456'
        self.DBNAME = 'ihealth'
        self.db = self.connect()
    def connect(self):
        try:
            con = pymysql.connect(self.DBHOST, self.DBUSER, self.DBPASSWORD, self.DBNAME)
            return con
        except pymysql.Error as e:
            logger.error('数据库连接失败！')

    def queryall(self):
        con = self.db
        cur = con.cursor()
        sql = 'select * from user'
        cur.execute(sql)
        data = cur.fetchall()
        return data

    def closedb(self):
        self.db.close()
