import scrapy
from ..items import MovieItem


class MovieSpider(scrapy.Spider):
    name = "movie"
    allowed_domains = ["movie.douban.com"]
    base_url = ""
    start_urls = []
    custom_settings = {
        'ITEM_PIPELINES': {
            'api_basic.interfaces.crawler.tutorial.pipelines.DoubanMoviePipeline': 300,
        },
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'
    }

    def __init__(self, actor, base_path, *args, **kwargs):
        super(MovieSpider, self).__init__(*args, **kwargs)
        self.actor = actor
        self.base_path = base_path
        self.base_url = "https://movie.douban.com/celebrity/{0}/movies".format(
            actor['id'])
        self.start_urls = [
            "https://movie.douban.com/celebrity/{0}/movies?start=0&format=text&sortby=time&".format(
                actor['id'])
        ]

    def parse(self, response):
        for sel in response.xpath('//table/tbody/tr'):
            item = MovieItem()
            item['title'] = sel.xpath(
                'td[@headers="m_name"]/a/text()').extract_first()
            item['link'] = sel.xpath(
                'td[@headers="m_name"]/a/@href').extract_first()
            item['date'] = sel.xpath(
                'td[@headers="mc_date"]/text()').extract_first()
            item['rating'] = sel.xpath(
                'td[@headers="mc_rating"]/div/span[@class="rating_nums"]/text()').extract_first()
            yield item
        next_url = response.xpath(
            '//span[@class="next"]/a/@href').extract_first()
        if next_url:
            yield scrapy.Request(self.base_url + next_url, callback=self.parse)
