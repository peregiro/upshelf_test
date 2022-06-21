# -*- coding: utf-8-*-
import scrapy
from scrapy.loader import ItemLoader
from upshelf_test.items import Product
from scrapy import Request

class TestIphone(scrapy.Spider):

    name = "test_iphone"
    allowed_domains = ["target.com"]
    start_urls = ['https://www.target.com/p/apple-iphone-13-pro-max/-/A-84616123?preselect=84240109#lnk=sametab']

    questions = []
    count_pages_questions = 0
    product_id = None

    URL_QUESTIONS = 'https://r2d2.target.com/ggc/Q&A/v1/question-answer?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&page=0&questionedId={}&type=product&size=100&sortBy=MOST_ANSWERS&errorTag=drax_domain_questions_api_error'
    URL_PRICE = 'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={}&is_bot=false&member_id=0&store_id=1233&pricing_store_id=1233&has_pricing_store_id=true&has_financing_options=true&visitor_id=018180B1D5870201B0D97CF4134E702D&has_size_context=true&latitude=42.830&longitude=-1.690&zip=31160&state=NA'


    def parse(self, response):

        l = ItemLoader(item=Product(), response=response)
        l.add_xpath('name', '//meta[@property="og:title"]/@content')
        l.add_xpath('description', '//div[@data-test="item-details-description"]//text()')
        l.add_xpath('highlights', '//h3[text()="Highlights"]/../ul//text()')
        l.add_xpath('specifications', '//div[@data-test="item-details-specifications"]/div//text()')
        l.add_xpath('images_urls', '//div[@data-test="carousel"]//img[contains(@src, "/image/")]/@src')

        route_variant_id = '(//b[text()="TCIN"]/../text())[last()]'
        variant_id = response.xpath(route_variant_id).extract()[0]

        route_product_id = '//syndigo-powerpage/@pageid'
        self.product_id = response.xpath(route_product_id).extract()[0]

        yield Request(
            url=self.URL_PRICE.format(self.product_id),
            callback=self.parse_item_price,
            meta={
                'item': l,
                'variant_id': variant_id
            }
        )


    def parse_item_price(self, response):
        
        json_data = response.json()
        price = self.extract_price(response.meta.get('variant_id'), json_data)
        item = response.meta.get('item')
        item.add_value('price', price)
        
        yield Request(
            url=self.URL_QUESTIONS.format(self.product_id),
            callback=self.parse_item_questions,
            meta={
                'item': item
            }
        )

    def extract_price(self, variant_id, json_data):
        variants = json_data.get('data').get('product').get('children')
        for variant in variants:
            if variant.get('tcin') == variant_id:
                return variant.get('price').get('current_retail')

    def parse_item_questions(self, response):
        json_data = response.json()
        item = response.meta.get('item')
        
        self.questions += self.extract_questions(json_data)

        num_extra_pages_results = self.get_num_extra_pages_results(json_data)
        yield from self.extra_pages_questions(num_extra_pages_results, item, response.url)

        if self.count_pages_questions >= num_extra_pages_results+1:
            item.add_value('questions', self.questions)
            yield item.load_item()

    def extract_questions(self, json_data):

        self.count_pages_questions += 1
        results_questions = json_data.get('results')
        questions = []
        for result in results_questions:
            question = result.get('text')
            answers = [answer.get('text') for answer in result.get('answers')]
            question = {
                'question': question,
                'answers': answers
            }
            questions.append(question)

        return questions

    def get_num_extra_pages_results(self, json_data):
        total_results = json_data.get('total_results')
        max_results = 100
        return int(total_results/max_results)

    def extra_pages_questions(self, num_extra_pages_results, item, url):

        if 'page=0' in url and num_extra_pages_results > 0:
            for page in range(num_extra_pages_results):
                url = self.URL_QUESTIONS.format(self.product_id).replace('page=0', 'page={}'.format(page+1))
                yield Request(
                    url=url,
                    callback=self.parse_item_questions,
                    meta={
                        'item': item,
                    }
                )