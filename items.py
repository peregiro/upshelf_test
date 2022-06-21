import scrapy


class Product(scrapy.Item):
    name = scrapy.Field()
    description = scrapy.Field()
    highlights = scrapy.Field()
    specifications = scrapy.Field()
    questions = scrapy.Field()
    images_urls = scrapy.Field()
    price = scrapy.Field()
