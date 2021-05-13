# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
from ..CONST import ACTOR_FILE, MOVIE_FILE
from pathlib import Path


class DoubanMoviePipeline(object):

    def __init__(self):
        self.movies = []

    def process_item(self, item, spider):
        self.movies.append(dict(item))
        return item

    def close_spider(self, spider):
        Path(spider.base_path + '/movies/').mkdir(parents=True, exist_ok=True)
        with open(spider.base_path + '/movies/'+spider.actor['name']+'.json', 'w') as f:
            data = json.dumps(self.movies) + "\n"
            f.write(data)


class DoubanActorPipeline(object):
    def __init__(self):
        self.actors = []

    def process_item(self, item, spider):
        self.actors.append(dict(item))
        return item

    def close_spider(self, spider):
        with open(spider.base_path + '/'+ACTOR_FILE, 'w') as f:
            data = json.dumps(self.actors)
            f.write(data)
