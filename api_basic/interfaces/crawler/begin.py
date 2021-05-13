# 引用spider
from tutorial.spiders.movie_spider import MovieSpider
from tutorial.spiders.actor_spider import ActorSpider

from twisted.internet import reactor, defer

from scrapy.crawler import CrawlerRunner
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
import json
from CONST import ACTOR_FILE, MOVIE_FILE, ACTOR_NAME_FILE

configure_logging()
runner = CrawlerRunner(get_project_settings())


@defer.inlineCallbacks
def crawl():
    with open(ACTOR_NAME_FILE, "r", encoding='utf-8') as f:
        datas = json.load(f)
        actors = []
        for data in datas:
            if data['result']:
                actors.append(data['result'][0]['label'])
    yield runner.crawl(ActorSpider, actors)

    with open(ACTOR_FILE, "r", encoding='utf-8') as f:
        datas = json.load(f)
        for data in datas:
            yield runner.crawl(MovieSpider, data)
    reactor.stop()


crawl()
reactor.run()  # the script will block here until the last crawl call is finished
