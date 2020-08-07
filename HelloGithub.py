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


class HelloGithub:

    def __init__(self, headers, cookies):
        self.header = {headers.split(': ')[0]: headers.split(': ')[1]}
        self.cookie = {}
        for i in cookies.split("; "):
            self.cookie[i.split('=')[0]] = i.split('=')[1]
        mongo = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = mongo['hellogithub']
        self.proxy = get_proxies()

    def get_github(self, segment='python 项目'):
        table = self.db['项目']
        table.create_index('uid')

        cur_pg = 1
        n = 0
        has_next = True
        seg = segment if " " not in segment else segment.split(' ')[0]
        got = table.distinct('url')
        start = time.time()
        while has_next:
            url = f'https://hellogithub.com/periodical/category/{segment}/?page={cur_pg}'
            r = req_get(url, header=self.header, proxy=self.proxy)
            soup = BeautifulSoup(r.text, 'lxml')
            next_btn = soup.find_all('div', class_='next')
            if len(next_btn) == 0:
                has_next = False
            cur_pg += 1

            items = soup.find_all('h2', class_='content-subhead')
            for item in items:
                # 条目预处理
                item.find_next('p').find('strong').clear()
                temp_url = item.find('a', class_='project-url')['href']
                if temp_url in got:
                    continue
                try:
                    img_url = item.find_next('p').find_next('img')['src']
                    if img_url.split('/')[-1].split('.')[0] != item.find('a', class_='project-url').text.strip():
                        img_url = ''
                except TypeError:
                    img_url = ''
                temp_r = req_get(temp_url, header=self.header, proxy=self.proxy, retry=15)
                if not temp_r:
                    continue
                temp_soup = BeautifulSoup(temp_r.text, 'lxml')
                info = re.sub(r'\s+', ' ', temp_soup.find('ul', class_="pagehead-actions").text)
                fork = re.search(r'Fork (.+)', info).group(1).strip()
                star = re.search(r'Star (.+?) ', info).group(1).strip()
                watch = re.search(r'Watch (.+?) ', info).group(1).strip()

                # 获取数据
                github = dict()
                github['title'] = item.find('a', class_='project-url').text.strip()
                github['url'] = temp_url
                github['abstract'] = item.find_next('p').text.strip()
                github['uid'] = temp_url
                github['keyword'] = 'C#' if seg == "C%23" else "C++" if seg == "%2B%2B" else seg
                github['fork'] = int(float(fork.strip('k')) * 1000) if fork.endswith('k') else int(fork)
                github['star'] = int(float(star.strip('k')) * 1000) if star.endswith('k') else int(star)
                github['watch'] = int(float(watch.strip('k')) * 1000) if watch.endswith('k') else int(watch)
                github['img_url'] = img_url
                table.update_one({"uid": github['uid']}, {"$set": github}, True)
                n += 1
                end = time.time()
                spend = end - start
                print(f"\r进度: 获得{n}条课程数据"
                      f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, ", end='')

        print(f"\r爬取课程数据完成, 共获取{n}条数据")
        return None

    def update_star(self):
        table = self.db['项目']
        table.create_index('uid')

        urls = table.distinct('uid')
        start = time.time()
        for e, url in enumerate(urls):
            github = dict()
            r = req_get(url, header=self.header, proxy=self.proxy, retry=15)
            if not r:
                continue
            soup = BeautifulSoup(r.text, 'lxml')
            info = re.sub(r'\s+', ' ', soup.find('ul', class_="pagehead-actions").text)
            fork = re.search(r'Fork (.+)', info).group(1).strip()
            star = re.search(r'Star (.+?) ', info).group(1).strip()
            watch = re.search(r'Watch (.+?) ', info).group(1).strip()
            github['fork'] = int(float(fork.strip('k')) * 1000) if fork.endswith('k') else int(fork)
            github['star'] = int(float(star.strip('k')) * 1000) if star.endswith('k') else int(star)
            github['watch'] = int(float(watch.strip('k')) * 1000) if watch.endswith('k') else int(watch)
            table.update_one({"uid": url}, {"$set": github}, True)
            end = time.time()
            spend = end - start
            unit_spend = spend / (e + 1)
            remain = (len(urls) - e - 1) * unit_spend
            print(f"\r进度({e + 1}/{len(urls)}), 已更新{e + 1}条开源库数据, "
                  f"用时{int(spend // 3600)}:{int(spend % 3600 // 60)}:{int(spend % 60)}, "
                  f"预计还剩{int(remain // 3600)}:{int(remain % 3600 // 60)}:{int(remain % 60)}.", end='')
        print(f"爬取开源库信息完成, 共获取{e + 1}条数据")


if __name__ == "__main__":
    c = "_ga=GA1.2.210637442.1591870960; _gid=GA1.2.694650607.1592025544; session=f7485d25-5689-4715-a071-4b33b3a1388e.w4PLelDxRjrJtCRM5-U5QN3Jue0; Hm_lvt_73e0d9a1bd6e22a206afe0551e5e603d=1591871070,1592025545,1592105849,1592106566; Hm_lpvt_73e0d9a1bd6e22a206afe0551e5e603d=1592125356"
    h = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'

    langs = ['Python 项目', 'C 项目', 'C%23 项目', 'C%2B%2B 项目', 'css 项目', 'Go 项目', 'Java 项目', 'JavaScript 项目',
             'Kotlin 项目', 'Objective-c 项目', 'PHP 项目', 'Ruby 项目', 'Rust 项目', 'Swift 项目', '其它', '开源书籍', '教程', '机器学习']
    hg = HelloGithub(headers=h, cookies=c)
    # hg.update_star()
    for i in langs:
        print(i)
        hg.get_github(segment=i)
