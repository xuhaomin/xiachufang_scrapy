# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 22:13:25 2017

@author: Administrator
"""

import scrapy
from ..items import xiachufang_Recipe

import re

category_re = re.compile(r"cat(\d+)")
high_value_recipe_re = re.compile(r"/recipe/(\d+)/")

class xiachufang_Spider(scrapy.Spider):
    name = "xiachufang"
    allowed_domains = []
    start_urls = ['http://www.xiachufang.com/category/']

    def parse(self,response):
        category_id = response.xpath('//li[contains(@id,"cat")]/@id').re(category_re)
        for i in category_id:
            for j in range(1,4):
                url = "http://www.xiachufang.com/category/%s/time/?page=%d"%(i,j)
                yield scrapy.Request(url,callback = self.parse2)

    def parse2(self,response):
        high_value_recipe = response.xpath('//a[@class="image-link"]/@href').re(high_value_recipe_re)
        for i in high_value_recipe:
            url = 'http://www.xiachufang.com/recipe/%s/'%i
            yield scrapy.Request(url,callback = self.parse_item)


    def parse_item(self, response):     
        if response.status==200:       
            item = xiachufang_Recipe()
            try:
                item['name'] = response.xpath('//h1[@class="page-title"]/text()').extract()[0].replace(' ','').replace('\n','')
            except:
                item['name'] = response.xpath('//h1[@class="page-title"]/text()').extract()
            item['ratingValue'] = response.xpath('//span[@itemprop="ratingValue"]/text()').extract()
            item['popularity'] = response.xpath('//div[@class="cooked"]').xpath('.//span[@class="number"]/text()').extract()
            item['description'] = response.xpath('//div[@class="desc"]/text()').extract()
            item['description'] = item['description'][0].replace(' ','').replace('\n','') if item['description'] else None
            temp = []
            for ingerdient in response.xpath('//tr[@itemprop="recipeIngredient"]'):  
                name = ingerdient.xpath('td[contains(@class,"name")]').xpath('string(.)').extract()[0].replace(' ','').replace('\n','')
                unit = ingerdient.xpath('td[contains(@class,"unit")]').xpath('string(.)').extract()[0].replace(' ','').replace('\n','')
                temp.append( {"材料":name,"用量":unit})
            item['recipeIngredient'] = temp
            item['steps'] = response.xpath('//div[@class="steps"]/ol')[0].xpath('string(.)')[0].extract().replace(' ','').replace('\n','')
            item['url'] = response.url
            item['tip'] = response.xpath('//div[@class="tip"]')[0].xpath('string(.)')[0].extract().replace(' ','').replace('\n','')  if response.xpath('//div[@class="tip"]') else ''
            yield item
