# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
import config

class Spiders100Pipeline(object):
    def __init__(self):
      self.conn = MySQLdb.connect(
        user = DB_xiachufang['user'],
        passwd = DB_xiachufang['passwd'],
        db= DB_xiachufang['db'],
        host= DB_xiachufang['host'],
        charset= DB_xiachufang['charset'],
        use_unicode= DB_xiachufang['use_unicode']
        )


    def process_item(self, item, spider):
      cursor = self.conn.cursor()

      name = item['name']
      ratingValue = float(item['ratingValue'][0]) if item['ratingValue'] else 0
      popularity = int(item['popularity'][0]) if item['popularity'] else 0
      recipeIngredient = str(item['recipeIngredient']).replace(',','~').replace('\'','')
      description = item['description']
      steps = item['steps']
      url = item['url']
      tip = item['tip']

      sql = """INSERT INTO %s.%s (name, ratingValue, popularity, \
      recipeIngredient, description, steps, url, tip) \
      VALUES ('%s', '%d', '%d', '%s', '%s', '%s', '%s','%s')"""\
      %(DB_xiachufang['db'],DB_xiachufang['table'],name, ratingValue, popularity,recipeIngredient, description, steps, url,tip)
      try:
         cursor.execute(sql)
         self.conn.commit()
      except:
         self.conn.rollback()
         print("error")
      return item

    def close_spider(self,spider):

      self.conn.close()