import random
import re
import time
import warnings
import requests
import pymongo
from bs4 import BeautifulSoup
import pandas as pd

from Base import *

warnings.filterwarnings("ignore")


class ShiYanLou:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['实验楼']
        self.proxy = get_proxies()

    def get_course(self):
        table = self.db['项目']
        table.create_index('uid')

        error = 0
        n = 1
        start = time.time()
        while error <= 1000:
            if n in table.distinct('uid'):
                print(f'\r{n}', end='')
                continue
            url = f'https://www.shiyanlou.com/courses/{n}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            if not r:
                error += 1
                n += 1
                continue
            soup = BeautifulSoup(r.text, 'lxml')

            course = dict()
            course['url'] = url
            course['uid'] = n
            course['title'] = soup.h1.text.strip()
            if course['title'] == '':
                continue
            course['learned'] = re.search(r'(\d+) 人学过', soup.find('div', class_='info-body').text).group(1)
            course['follow'] = re.search(r'(\d+) 人关注', soup.find('div', class_='info-body').text).group(1)
            course['author'] = re.search(r'作者: (.+)', soup.find('div', class_='info-body').text).group(1)
            course['abstract'] = soup.find('p', class_='info-desc font-15 color-text').text.strip()
            course['type'] = soup.find('span', class_='course-type-tag').text.strip()
            course['keyword'] = str()
            course['knowledge'] = str()
            keywords = soup.find('ol', class_="breadcrumb").find_all('li')[1:]
            for keyword in keywords[:-1]:
                course['keyword'] += keyword.text.strip() + ', '
            try:
                knowledge = soup.find('section', class_='section section-points').find_all('li')
                for know in knowledge:
                    course['knowledge'] += know.text.strip() + ', '
            except AttributeError:
                pass
            try:
                course['price'] = re.search(r'(\d+)', soup.find('span', class_='real-price').text).group(1)
            except AttributeError:
                course['price'] = '0'
            course['img_url'] = soup.find('div', class_="box-body-top course-cover").find('img')['src']
            table.update_one({"uid": course['uid']}, {"$set": course}, True)
            end = time.time()
            spend = end - start
            print(f"\r进度: 获得{n}条课程数据, 返回{error}个错误"
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, ", end='')
            n += 1
        print(f"\r爬取课程数据完成, 共获取{n}条数据")


if __name__ == "__main__":
    h = 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    c = "DSID=AAO-7r68PLyYRqcipZ1L5OVp3UC83mTmgwKY8P6pdLSTTpaK9lpF3S6T6ox9XCE7AaRHRl0am_tDFbxjgflnRvJwkiRJ909Zh6l5LiwUMIvZ1pok4Qu3VHY; IDE=AHWqTUmyhgepu8kEpAk7zfVbep70Po7zc2aPub2ScLOVi1LE102G4JwvvDft8a3k"
    syl = ShiYanLou(headers=h, cookies=c)
    syl.get_course()
