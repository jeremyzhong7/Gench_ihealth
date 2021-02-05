import os
import pickle

import requests
from Health_logger import logger
from fake_useragent import UserAgent
from lxml import etree
import json
import db


class Student_health:
    def __init__(self, username):
        self.username = username
        self.password = ''
        self.info = ''  # 昨天打卡的信息抓取
        self.login_URL = 'https://cas.gench.edu.cn/cas/login?service=http%3A%2F%2Fi1.gench.edu.cn%2F_web%2Ffusionportal%2Fwelcome.jsp%3F_p%3DYXM9MSZwPTEmbT1OJg__'
        self.stu_URL = 'http://i1.gench.edu.cn/_web/fusionportal/stu/index.jsp?_p=YXM9MSZwPTEmbT1OJg__'  # 最终学生登录页面
        self.headers = {
            'User-Agent': UserAgent().chrome
        }
        self.session = requests.Session()
        self.login_form = {}
        self.Has_local_cookies = False
        self.cookies_dir_path = "./cookies/"  # cookies的存放路径
        self.load_cookies_from_local()  # 检测本地是否存在cookie(gench_user) 首次为None

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


    '''
    登入系统
    '''

    def login(self):
        # logger.info('进入login方法')
        self.login_form['username'] = self.username
        self.login_form['password'] = self.password
        session = self.session
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

    def health_daily(self):
        session = self.session
        # session.headers.pop('Referer')

        try:
            if not self.Has_local_cookies:
                session.headers['Referer'] = 'http://ihealth.hq.gench.edu.cn/pc/login-student'
                session.get('http://ihealth.hq.gench.edu.cn/api/login/student')  # 拿到gench_hq_user
                self.save_cookies_to_local(self.username)
                # print(session.cookies)
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


    """
    cookie相关操作
    保存和读取
    """
    def get_cookies(self):
        """
        获取当前Cookies
        :return:
        """
        return self.session.cookies

    def set_cookies(self, cookies):
        self.session.cookies.update(cookies)

    def load_cookies_from_local(self):
        """
        从本地加载Cookie
        :return:
        """

        cookies_file = ''
        if not os.path.exists(self.cookies_dir_path):
            return None
        for name in os.listdir(self.cookies_dir_path):
            '''
            如果该cookies文件是由该学号开头，则认为该学号之前的cookies已保存到本地
            '''
            if name.startswith(self.username):
                cookies_file = '{}{}'.format(self.cookies_dir_path, name)
                break
        if cookies_file == '':
            return None
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.set_cookies(local_cookies)
        self.Has_local_cookies = True

    def save_cookies_to_local(self, cookie_file_name):
        """
        保存Cookie到本地
        :param cookie_file_name: 存放Cookie的文件名称
        :return:
        """
        cookies_file = '{}{}.cookies'.format(self.cookies_dir_path, cookie_file_name)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.get_cookies(), f)

if __name__ == '__main__':

    # 数据库中拿学号密码信息
    db = db.db()
    users = db.queryall()
    db.closedb()

    infos = [{'username': user[0],
              'password': user[1]} for user in users]

    # 若用户较多建议改用多进程实现同时打卡 若只有一核的服务器 就不必多折腾
    for s in infos:
        stu = Student_health(s['username'])
        # stu.username = s['username']  # 学号

        """
        有Cookies直接登录i健康进行打卡
        没有则通过信息门户进入i健康
        """

        if stu.Has_local_cookies:
            stu.health_daily()
        else:
            stu.password = s['password']  # 密码

            stu.login_parse()
            flag = stu.login()
            if flag:
                stu.health_daily()
