import re
import scrapy
from datetime import datetime


class PharmacySpider(scrapy.Spider):
    name = 'lek_opt_torg'
    allowed_domains = ['lekopttorg.ru']
    start_urls = [
        'https://lekopttorg.ru/catalog/lekarstva_i_profilakticheskie_sredstva/vitaminy_i_mineraly/',
        'https://lekopttorg.ru/catalog/lekarstva_i_profilakticheskie_sredstva/pri_allergii/'
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        urls = response.xpath('//div[@class="product"]/a/@href').getall()
        for url in urls:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, callback=self.parse_details)

        next_page = response.xpath('//div[@class="pagination"]/a/@href').get()
        if next_page:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(url=next_page, callback=self.parse)

    def parse_details(self, response):
        rpc = response.xpath("//div[@class='card-slider']/a[contains(@class, 'favorite_link')]/@data-id").get()
        title = response.xpath('//h1/text()').get().strip()
        brand = response.xpath('//span[@class="text-link"]/a/text()').get()
        section = response.xpath("//div[@itemprop='itemListElement']/span/a/@title").getall()

        price = response.xpath('//div[@itemprop="offers"]/span[contains(@class, "slider-price")]/text()').get()
        price = int(re.findall('\d+', price)[0])

        availability = response.xpath('//div[@class="av-sidebar"]')
        if availability:
            in_stock = True
        else:
            in_stock = False

        assets = {'main_image': '', 'all_images': []}
        all_images = response.xpath('//div[@class="card-slider-g__pic"]//img/@src').getall()
        if all_images:
            assets['main_image'] = all_images[0]
            assets['all_images'] = all_images

        metadata_dict_keys = response.xpath('//div[@class="card__key-val"]//span[@class="key"]/text()').getall()[:-1]
        metadata_dict_keys = [key.replace('\n', '').strip(': ') for key in metadata_dict_keys]
        metadata_dict_keys = [key for key in metadata_dict_keys if key != '']

        metadata_dict_values = response.xpath('//div[@class="card__key-val"]//span[@class="val"]/text() |'
                                              '//div[@class="card__key-val"]//span[@class="text-link"]//a/text()').getall()
        metadata_dict_values = [value.replace('\n', '').strip(': ') for value in metadata_dict_values]

        metadata_dict = dict(zip(metadata_dict_keys, metadata_dict_values))

        yield {
            'timestamp': datetime.now(),
            'RPC': rpc,
            'url': response.url,
            'title': title,
            'brand': brand,
            'section': section,
            'price': price,
            'in_stock': in_stock,
            'assets': assets,
            'metadata': metadata_dict,
        }
