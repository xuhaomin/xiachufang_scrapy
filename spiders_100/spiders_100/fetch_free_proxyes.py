#!/usr/bin/python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import urllib.request
import logging
import re
import threading
from multiprocessing import Pool
import os

from . import config

logger = logging.getLogger(__name__)


class proxyGet(object):

    def __init__(self,url="http://www.baidu.com/js/bdsug.js?v=1.0.3.0"):
        self.valid_proxyes = ()
        self.proxyes = []
        self.pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{1,4}")
        self.url = url

    def get_html(self,url):
        request = urllib.request.Request(url,headers= config.HEADER)
        html = urllib.request.urlopen(request)
        return html.read()

    def get_soup(self,url):
        soup = BeautifulSoup(self.get_html(url), "lxml")
        return soup

    def fetch_kxdaili(self,page):
        """
        从www.kxdaili.com抓取免费代理
        """
        try:
            logger.info("fetching from kxdaili......")  
            url = "http://www.kxdaili.com/dailiip/1/%d.html" % page
            soup = self.get_soup(url)
            table_tag = soup.find("table", attrs={"class": "segment"})
            trs = table_tag.tbody.find_all("tr")
            for tr in trs:
                tds = tr.find_all("td")
                ip = tds[0].text
                port = tds[1].text
                latency = tds[4].text.split(" ")[0]
                if float(latency) < 0.5: # 输出延迟小于0.5秒的代理
                    proxy = "%s:%s" % (ip, port)
                    self.proxyes.append(proxy)
        except:
            logger.warning("fail to fetch from kxdaili")

    def img2port(self,img_url):
        """
        mimvp.com的端口号用图片来显示, 本函数将图片url转为端口, 目前的临时性方法并不准确
        """
        code = img_url.split("=")[-1]
        if code.find("AO0OO0O")>0:
            return 80
        else:
            return None

    def fetch_mimvp(self,page = 1):
        """
        从http://proxy.mimvp.com/free.php抓免费代理
        """
        try:
            logger.info("fetching from mimvp......")    
            url = "http://proxy.mimvp.com/free.php?proxy=in_hp&sort=&page=%d" % page
            soup = self.get_soup(url)
            table = soup.find("div", attrs={"id": "list"}).table
            tds = table.tbody.find_all("td")
            for i in range(0, len(tds), 10):
                id = tds[i].text
                ip = tds[i+1].text
                port = self.img2port(tds[i+2].img["src"])
                response_time = tds[i+7]["title"][:-1]
                transport_time = tds[i+8]["title"][:-1]
                if port is not None and float(response_time) < 1 :
                    proxy = "%s:%s" % (ip, port)
                    self.proxyes.append(proxy)
        except:
            logger.warning("fail to fetch from mimvp")

    def fetch_xici(self,page):
        """
        http://www.xicidaili.com/nn/
        """
        try:
            logger.info("fetching from xici......")    
            url = "http://www.xicidaili.com/nn/%d" % page
            soup = self.get_soup(url)
            table = soup.find("table", attrs={"id": "ip_list"})
            trs = table.find_all("tr")
            del(trs[0])
            for tr in trs:
                tds = tr.find_all("td")
                ip = tds[1].text
                port = tds[2].text
                speed = tds[6].div["title"][:-1]
                latency = tds[7].div["title"][:-1]
                if float(speed) < 3 and float(latency) < 1:
                    self.proxyes.append("%s:%s" % (ip, port))
        except Exception as e:
            logger.warning("fail to fetch from xici: %s" % e)

    def fetch_ip181(self,page = 1):
        """
        http://www.ip181.com/
        """
        try:
            logger.info("fetching from ip181......")    
            url = "http://www.ip181.com/daili/%d.html" % page
            soup = self.get_soup(url)
            table = soup.find("table")
            trs = table.find_all("tr")
            for i in range(1, len(trs)):
                tds = trs[i].find_all("td")
                ip = tds[0].text
                port = tds[1].text
                latency = tds[4].text[:-2]
                if float(latency) < 1:
                    self.proxyes.append("%s:%s" % (ip, port))
        except Exception as e:
            logger.warning("fail to fetch from ip181: %s" % e)

    def fetch_httpdaili(self):
        """
        http://www.httpdaili.com/mfdl/
        更新比较频繁
        """ 
        logger.info("fetching from httpdaili......")       
        url = "http://www.httpdaili.com/mfdl/"
        soup = self.get_soup(url)
        trs = []
        for i in soup.find_all("div", attrs={"kb-item-wrap11"}):
            for index,item in enumerate(i.table.find_all("tr")):
                if index != 0:
                    trs.append(item)
        try:
            for tr in trs:
                tds = tr.find_all("td")
                if len(tds)>2:
                    ip = str(tds[0].text)
                    port = str(tds[1].text)
                    anony = tds[2].text
                    if anony == u"匿名":
                        self.proxyes.append("%s:%s" % (ip, port))
        except Exception as e:
            logger.warning("fail to fetch from httpdaili: %s" % e)        


    def fetch_66ip(self,page):
        """    
        http://www.66ip.cn/
        每次打开此链接都能得到一批代理, 速度不保证
        """
        try:
            logger.info("fetching from 66ip......")
            # 修改getnum大小可以一次获取不同数量的代理
            url = "http://www.66ip.cn/nmtq.php?getnum=%d" % 20*page
            soup = self.get_soup(url)
            pros = self.pattern.findall(soup.find("body").text)
            for pro in pros:
                self.proxyes.append(pro)

        except Exception as e:
            logger.warning("fail to fetch from 66ip: %s" % e)

    def fetch_mimi(self,page = 1):
        """    
        http://www.mimiip.com/
        """
        try:
            logger.info("fetching from mimiip......")
            url = "http://www.mimiip.com/gngao/%d" % page
            soup = self.get_soup(url)
            table = soup.find("table",attrs={"class": "list"})
            trs = table.find_all("tr")
            for i in range(1, len(trs)):
                tds = trs[i].find_all("td")
                ip = tds[0].text
                port = tds[1].text
                self.proxyes.append("%s:%s" % (ip, port))
        except Exception as e:
            logger.warning("fail to fetch from mimiip: %s" % e)

    def check(self,proxy):
        proxy_handler = urllib.request.ProxyHandler({'http': "http://" + proxy})
        opener = urllib.request.build_opener(proxy_handler,urllib.request.HTTPHandler)
        try:
            response = opener.open(self.url,timeout=3)
            if response.code == 200:
                return proxy
        except Exception:
            return

    def fetch_all(self,endpage=2):

        func_pool = Pool(4)
        for i in range(1, endpage):
            func_pool.apply_async(self.fetch_kxdaili(i))
            func_pool.apply_async(self.fetch_mimvp(i))
            func_pool.apply_async(self.fetch_ip181(i))
            func_pool.apply_async(self.fetch_xici(i))
            func_pool.apply_async(self.fetch_mimi(i))
        func_pool.apply_async(self.fetch_66ip(i))
        func_pool.apply_async(self.fetch_httpdaili())
        func_pool.close()
        func_pool.join()
      
        logger.info("checking proxyes validation, total:%d"%len(self.proxyes))
        pool = Pool(50)
        self.valid_proxyes = set(pool.map(self.check,self.proxyes)) - {None}
        logger.info("fetch valid proxyes total:%d"%len(self.valid_proxyes))
        pool.close()
        pool.join()
        return list(self.valid_proxyes)



if __name__ == '__main__':
    import sys
    root_logger = logging.getLogger("")
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(name)-8s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    my_proxy = proxyGet('http://www.google.com/')
    proxyes = my_proxy.fetch_all()
    print(proxyes)
