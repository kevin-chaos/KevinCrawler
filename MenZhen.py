import time
import warnings

import pymongo
from bs4 import BeautifulSoup

from Base import *

warnings.filterwarnings("ignore")


class MenZhen:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['门诊网']
        self.proxy = get_proxies()

    def get_meeting(self):
        def fetch_meetings():
            years = [2020, 2019, 2018]
            meeting = list()
            for y in years:
                link = f'http://www.menzhen.org/site/meeting.html?y={y}'
                r = req_get(link, header=self.header)
                soup = BeautifulSoup(r.text, 'lxml')
                items = soup.find('div', class_='l').find_all('dd')

                for i in items:
                    date = re.search(r'(\d{4}年\d{2}月)', i.find('div', class_='f12 cblack').text.strip()).group()
                    url = f'http://www.menzhen.org' + i.find('a')['href']
                    name = i.find('p').text
                    meeting.append((url, name, date))
            return meeting

        def fetch_details(url):
            r = req_get(url, header=self.header)
            soup = BeautifulSoup(r.text, 'lxml')
            items = soup.find_all('div', class_='meetingplace')

            detail = list()
            for i in items:
                content = i.find('div', class_='f15 cblack').text.strip()
                speaker = i.find('span', class_='cblack').text.strip().replace('> > ', '')
                link = f'http://www.menzhen.org' + i.find('a')['href']
                detail.append((content, speaker, link))

            return detail

        table = self.db['会议']
        table.create_index('uid')
        # 获取大会清单列表，包含url、date、name
        meetings = fetch_meetings()

        # 获取回访清单
        n = 0
        for ur, nm, da in meetings:

            details = fetch_details(ur)
            for cn, sp, lk in details:
                request = req_get(lk, header=self.header)
                if not request:
                    time.sleep(5)
                    continue
                bs = BeautifulSoup(request.text, 'lxml')
                try:
                    rd = re.search(r'浏览次数：(\d+)', bs.find('body').text).group(1)
                except AttributeError:
                    rd = '0'
                ent = {
                    "会议地址": ur,
                    "详情地址": lk,
                    "会议名称": nm,
                    "会议日期": da,
                    "会议内容": cn,
                    "主讲人": sp,
                    "浏览量": rd,
                    "uid": lk.split('=')[-1]
                }

                table.update_one({'uid': ent['uid']}, {"$set": ent}, True)
                n += 1
                print(n)
        return None


if __name__ == '__main__':
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
    c = 'Cookie: raysid=f101348914d55fc4; loc=ip=101.86.244.141&regionid=107'
    mz = MenZhen(headers=h, cookies=c)
    mz.get_meeting()
