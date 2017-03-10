# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class xiachufang_Recipe(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    name = scrapy.Field() 
    ratingValue = scrapy.Field()
    popularity = scrapy.Field()
    recipeIngredient = scrapy.Field()
    description = scrapy.Field() 
    steps = scrapy.Field()
    url = scrapy.Field()
    tip = scrapy.Field()
'''
下厨房菜谱:菜名,评分,人气,配料,步骤,链接
'''
