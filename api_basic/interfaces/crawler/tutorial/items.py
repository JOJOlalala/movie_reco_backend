# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MovieItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    rating = scrapy.Field()
    date = scrapy.Field()


class ActorItem(scrapy.Item):
    name = scrapy.Field()
    id = scrapy.Field()
    img = scrapy.Field()
    url = scrapy.Field()
