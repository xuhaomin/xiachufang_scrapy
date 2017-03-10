#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import logging
from datetime import datetime, timedelta
from twisted.web._newclient import ResponseNeverReceived
from twisted.internet.error import TimeoutError, ConnectionRefusedError, ConnectError
from .fetch_free_proxyes import proxyGet
import json

logger = logging.getLogger(__name__)


class node(object):

  def __init__(self,proxy,weight,next_node = None):
    self.proxy = proxy
    self.weight = weight
    self._next = next_node



class HttpProxyMiddleware(object):
    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ResponseNeverReceived, ConnectError, ValueError)

    def __init__(self, settings):


        '''
        代理列表的维护
        总表  list  proxyes = []
        当前的代理表 环形链表 proxyes_nodes 初始权重为 default_weight  当访问超时时,权重-1,当访问成功时权重+1,权重为0时出表
        当前可用代理数  valid_proxyes_num  小于 更新列表阈值 fetch_proxy_threshold 时 获取新的代理,插入链表
        不可用代理 list invalid_proxyes  
        '''

        #初始化总表
        self.url = "www.xiachufang.com"  #代理认证的url

        self.proxyes = []
        my_proxy = proxyGet(self.url)
        self.proxyes = my_proxy.fetch_all(3)

        #初始化链表
        self.valid_proxyes_num = len(self.proxyes)
        self.default_weight = 10
        self.proxy_under_use = self.proxyes_nodes = temp = node(None,self.default_weight)  #首元素为不用代理
        for proxy in self.proxyes:
            temp._next = node(proxy,self.default_weight)
            temp = temp._next
        temp._next = self.proxyes_nodes   #构建环形链表
        self.proxy_before = temp          #指向前一个链表的指针
        self.fetch_proxy_threshold = 10
        self.none_proxy_interval = 10  #设置一个不用代理的间隔,同时也是为了防止网址本身不能访问导致降低所有链表成员权重
        self.counter = 0 #为none_proxy_interval 设置的计数器
        #初始化不可用代理列表
        self.invalid_proxyes = []
        self.proxy_file = "proxy.json"  #将好用的代理存入文件

        #其他设置
        self.last_fetch_proxy_time = datetime.now()  #上次获取代理的时间



    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)


    def fetch_new_proxyes(self):
        """
        更新代理行为
        """
        logger.info("extending proxyes using fetch_free_proxyes.py")
        my_proxy = proxyGet(self.url)
        new_proxyes = []
        new_get = my_proxy.fetch_all()
        for np in new_get:
            if np not in self.proxyes:
                new_proxyes.append(np)
                self.proxyes.append(np)
        self.last_fetch_proxy_time = datetime.now()

        logger.info("fetch %d new proxyes" % len(new_proxyes))
        if  len(new_proxyes) < 1:
            logger.warning("no more valid proxyes I can fetch")  
            self.fetch_proxy_threshold -= 1
        else:
            #往链表中插入新代理
            for proxy in new_proxyes:
                temp = node(proxy,self.default_weight)
                self.proxy_before._next = temp
                temp._next = self.proxy_under_use
                self.proxy_before = temp
                self.valid_proxyes_num += 1   #可用代理数加一



    def process_request(self, request, spider):
        """
        将request设置为使用代理
        """
        request.meta["dont_redirect"] = True  # 禁止代理跳转
        self.counter = (self.counter + 1) % self.none_proxy_interval
        if self.counter:
            if self.proxy_under_use.weight > 0: #权重大于0,用该代理访问
                if self.proxy_under_use.proxy:
                    request.meta["proxy"] = "http://"+self.proxy_under_use.proxy
                    logger.info("build request use proxy %s" % self.proxy_under_use.proxy)
                elif "proxy" in request.meta.keys():
                    del request.meta["proxy"]
                    logger.info("build request not use proxy")
                if self.proxy_under_use.weight == 30:
                    with open(self.proxy_file, "a+") as fd:
                        fd.write(self.proxy_under_use.proxy + "/r/n")

            else:   #权重小于0,移除该代理,有效代理数-1
                self.valid_proxyes_num -= 1
                if self.valid_proxyes_num < self.fetch_proxy_threshold:
                    self.fetch_new_proxyes()  #当代理不足时,获取新代理
                logger.info("remove invaild proxy %s" % self.proxy_under_use.proxy)
                self.invalid_proxyes.append(self.proxy_under_use.proxy)
                self.proxy_under_use = self.proxy_under_use._next
                self.proxy_before._next = self.proxy_under_use
                if self.proxy_under_use.proxy:
                    request.meta["proxy"] = "http://"+self.proxy_under_use.proxy
                    logger.info("build request use proxy %s" % self.proxy_under_use.proxy)
                elif "proxy" in request.meta.keys():
                    del request.meta["proxy"]
                    logger.info("build request not use proxy")
        elif "proxy" in request.meta.keys():
                    del request.meta["proxy"]
                    logger.info("build request not use proxy")
        return
            

    def process_response(self, request, response, spider):
        # status不是正常的200而且不在spider声明的正常爬取过程中可能出现的
        # status列表中, 则认为代理无效, 切换代理, 并降低代理权重
        if response.status != 200  and  "proxy" not in request.meta.keys()\
                and (not hasattr(spider, "website_possible_httpstatus_list") \
                             or response.status not in spider.website_possible_httpstatus_list):
            logger.info("response status not in spider.website_possible_httpstatus_list")
            self.proxy_under_use.weight -= 1
            self.proxy_before = self.proxy_under_use
            self.proxy_under_use = self.proxy_under_use._next
            new_request = request.copy()
            return new_request
        elif "proxy" not in request.meta.keys():
            return response
        else:
            logger.info("success use proxy %s fetch item" % self.proxy_under_use.proxy)
            self.proxy_under_use.weight += 1
            self.proxy_before = self.proxy_under_use
            self.proxy_under_use = self.proxy_under_use._next           
            return response

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        logger.debug("raise exception: %s" % (exception))
        if "proxy" not in request.meta.keys():
            return response

        self.proxy_under_use.weight -= 1
        self.proxy_before = self.proxy_under_use
        self.proxy_under_use = self.proxy_under_use._next
        new_request = request.copy()
        return new_request

