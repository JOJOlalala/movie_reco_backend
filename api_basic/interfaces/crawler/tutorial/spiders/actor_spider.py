import scrapy
from ..items import ActorItem


class ActorSpider(scrapy.Spider):
    name = "actor"
    allowed_domains = ["movie.douban.com"]
    start_urls = []
    custom_settings = {
        'ITEM_PIPELINES': {
            'api_basic.interfaces.crawler.tutorial.pipelines.DoubanActorPipeline': 300,
        },
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'
    }

    def __init__(self, actors, base_path, *args, **kwargs):
        super(ActorSpider, self).__init__(*args, **kwargs)
        base_url = "https://movie.douban.com/celebrities/search?search_text="
        self.actors = actors
        self.base_path = base_path
        self.all_url = []
        for actor in actors:
            self.all_url.append(base_url+actor)
        self.start_urls = [self.all_url[0]]
        self.index = 0

    def parse(self, response):
        item = ActorItem()
        item['name'] = self.actors[self.index]
        res = response.xpath(
            '//a[@class="nbg"]/@href').extract_first()
        item['img'] = response.xpath(
            '//a[@class="nbg"]/img/@src').extract_first()
        item['url'] = res
        if res:
            item['id'] = res.split('/')[-2]
        yield item
        self.index += 1
        if self.index < len(self.all_url):
            yield scrapy.Request(self.all_url[self.index], callback=self.parse)
