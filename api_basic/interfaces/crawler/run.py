# 引用spider
from .tutorial.spiders.movie_spider import MovieSpider
from .tutorial.spiders.actor_spider import ActorSpider

from twisted.internet import reactor, defer

from scrapy.crawler import CrawlerRunner
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
import json
from .CONST import ACTOR_FILE, MOVIE_FILE, ACTOR_NAME_FILE

from multiprocessing import Process
from threading import Thread
from functools import wraps


# @defer.inlineCallbacks
# def crawl(base_path):
#     configure_logging()
#     runner = CrawlerRunner()

#     with open(base_path+'/'+ACTOR_NAME_FILE, "r", encoding='utf-8') as f:
#         datas = json.load(f)
#         actors = []
#         for data in datas:
#             if data['result']:
#                 actors.append(data['result'][0]['label'])
#     yield runner.crawl(ActorSpider, actors, base_path)

#     with open(base_path+'/'+ACTOR_FILE, "r", encoding='utf-8') as f:
#         datas = json.load(f)
#         for data in datas:
#             yield runner.crawl(MovieSpider, data, base_path)
#     reactor.stop()


# def run_crawl(base_path):
#     crawl(base_path)
#     # the script will block here until the last crawl call is finished
#     reactor.run(installSignalHandlers=0)

def actor_spider_f(base_path):
    try:
        process = CrawlerProcess()
        with open(base_path+'/'+ACTOR_NAME_FILE, "r", encoding='utf-8') as f:
            datas = json.load(f)
            actors = []
            for data in datas:
                if data['result']:
                    actors.append(data['result'][0]['label'])
            actors = list(set(actors))
        process.crawl(ActorSpider, actors, base_path)
        process.start()
    except Exception as e:
        print(e)


def movie_spider_f(base_path):
    try:
        process = CrawlerProcess()
        with open(base_path+'/'+ACTOR_FILE, "r", encoding='utf-8') as f:
            datas = json.load(f)
            for data in datas:
                process.crawl(MovieSpider, data, base_path)
        process.start()
    except Exception as e:
        print(e)


class testThread(Thread):
    def __init__(self, base_path):
        Thread.__init__(self)
        self.base_path = base_path

    def run(self):
        self._run_actor_spider()
        self._run_movie_spider()

    def _run_actor_spider(self):

        p = Process(target=actor_spider_f, kwargs={
                    "base_path": self.base_path})
        p.start()
        p.join()

    def _run_movie_spider(self):

        p = Process(target=movie_spider_f, kwargs={
                    "base_path": self.base_path})
        p.start()
        p.join()


def run_crawl(base_path):
    t = testThread(base_path)
    t.start()
    t.join()
