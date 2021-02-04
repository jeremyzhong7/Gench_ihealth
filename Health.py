import requests
from Health_logger import logger
from fake_useragent import UserAgent
from lxml import etree
import json
import db


class Student_health:
    def __init__(self):
        self.username = ''
        self.password = ''
        self.info = ''  # 昨天打卡的信息抓取
        self.login_URL = 'https://cas.gench.edu.cn/cas/login?service=http%3A%2F%2Fi1.gench.edu.cn%2F_web%2Ffusionportal%2Fwelcome.jsp%3F_p%3DYXM9MSZwPTEmbT1OJg__'
        self.stu_URL = 'http://i1.gench.edu.cn/_web/fusionportal/stu/index.jsp?_p=YXM9MSZwPTEmbT1OJg__'  # 最终学生登录页面
        self.headers = {
            'User-Agent': UserAgent().chrome
        }
        self.session = requests.Session()
        self.login_form = {}

    '''
    解析登录页面并抓取登录表单需要的参数
    '''

    def login_parse(self):
        # session = requests.Session()
        self.session.headers = self.headers
        try:
            resp = self.session.get(self.login_URL)
            e = etree.HTML(resp.text)
            self.login_form = {
                e.xpath('//*[@id="fm1"]/input[1]/@name')[0]: e.xpath('//*[@id="fm1"]/input[1]/@value')[0],
                e.xpath('//*[@id="encrypted"]/@name')[0]: e.xpath('//*[@id="encrypted"]/@value')[0],
                e.xpath('//*[@id="fm1"]/input[3]/@name')[0]: e.xpath('//*[@id="fm1"]/input[3]/@value')[0],
                e.xpath('//*[@id="fm1"]/input[4]/@name')[0]: e.xpath('//*[@id="fm1"]/input[4]/@value')[0]
            }
        except:
            logger.info('学号：' + self.username + '==================>登录出错')
        # print(self.session.cookies)

    def getsession(self):
        return self.session

    '''
    登入系统
    '''

    def login(self):
        # logger.info('进入login方法')
        self.login_form['username'] = self.username
        self.login_form['password'] = self.password
        session = self.getsession()
        # self.headers['Referer'] = 'http://i1.gench.edu.cn/_web/fusionportal/welcome.jsp?_p=YXM9MSZwPTEmbT1OJg__'
        # session.headers = self.headers
        session.headers['Referer'] = 'http://i1.gench.edu.cn/_web/fusionportal/welcome.jsp?_p=YXM9MSZwPTEmbT1OJg__'
        try:
            resp = session.post(self.login_URL, data=self.login_form, allow_redirects=False)
            # print(session.cookies)
            session.get(self.stu_URL)
            # print(session.cookies)
            if resp.status_code != 302:
                logger.info('学号：' + self.username + ' ======> 学号或密码错误')
                return False
            return True
        except:
            logger.info('学号：' + self.username + ' 登录异常')

    '''
    打卡模块
    '''

    def health(self):
        session = self.getsession()
        # session.headers.pop('Referer')
        session.headers['Referer'] = 'http://ihealth.hq.gench.edu.cn/pc/login-student'
        try:
            session.get('http://ihealth.hq.gench.edu.cn/api/login/student')  # 拿到gench_hq_user
            # print(session.cookies)
            # print(session.headers)
            resp = session.post('http://ihealth.hq.gench.edu.cn/api/GDaily/pageuseryestoday')
            self.info = json.loads(resp.text)['records'][0]
            # print(self.info)
            resp = session.post('http://ihealth.hq.gench.edu.cn/api/GDaily/add', data=self.info)
            # print(resp.text)
            final = json.loads(resp.text)
            if final['suc']:
                # logger.info('学号：' + self.info['userid'] + '打卡地点：' + self.info['slocation'] + self.info['location'] + '======>打卡成功!')
                logger.info('学号：{} 姓名：{} 打卡地点：{}-{} <打卡成功>'.format(self.info['userid'], self.info['username'],
                                                                   self.info['slocation'], self.info['location']))
        except:
            logger.info('学号：' + self.username + '======> <提交信息出错-打卡失败>')


if __name__ == '__main__':

    # 数据库中拿学号密码信息
    db = db.db()
    users = db.queryall()
    db.closedb()

    infos = [{'username': user[0],
              'password': user[1]} for user in users]

    # 改用多线程实现同时打卡
    for s in infos:
        stu = Student_health()
        stu.username = s['username']  # 学号
        stu.password = s['password']  # 密码

        stu.login_parse()
        flag = stu.login()
        if flag:
            stu.health()
