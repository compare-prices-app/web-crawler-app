from urllib.parse import urlencode

import scrapy
from parsel import Selector
import sys, os

from scrapy import Request
from scrapy.loader import ItemLoader

from Utils.PhoneDetailsGetter import PhoneDetailsGetter

sys.path.append(os.path.join(os.path.abspath('../')))
from models.Product import Product
from Utils import VexioXPaths

API_KEY = '9d620b9d-ba78-402a-90df-95465184cc14'


def get_proxy_url(url):
    payload = {'api_key': API_KEY, 'url': url}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url


class VexioCrawler(scrapy.Spider):
    name = "vexio_crawler"

    # allowed_domains = ["vexio.ro","www.vexio.ro"]

    # start_urls = ["https://www.vexio.ro/smartphone/"]

    def start_requests(self):
        start_url = "https://www.vexio.ro/smartphone/"
        yield scrapy.Request(url=get_proxy_url(start_url), callback=self.parse)

    def parse(self, response):
        item_links = []
        item_links = response.xpath(VexioXPaths.PRODUCT_BOX).getall()
        for item_link in item_links:
            selector = Selector(item_link)
            availability = selector.xpath(
                VexioXPaths.VexioXPaths.PRODUCT_AVAILABILITY).get().replace("\t", "").replace("\n", "")

            if "nu este in stoc" in availability.casefold():
                continue
            product = Product()
            product['main_site'] = "https://www.vexio.ro/"
            product['logo_url'] = "https://p1.akcdn.net/partnerlogosmall/41065.jpg"

            title = (selector.xpath(VexioXPaths.PRODUCT_MANUFACTURER).get() + " " +
                     selector.xpath(VexioXPaths.PRODUCT_NAME).get()).replace("\t", "").replace("\n", "")
            url = selector.xpath(VexioXPaths.PRODUCT_URL).get()
            price = selector.xpath(VexioXPaths.PRODUCT_PRICE).get().replace("\t", "").replace("\n",
                                                                                                          "").replace(
                "lei", "").strip()

            phone_details_getter = PhoneDetailsGetter()
            phone_details = phone_details_getter.get_details(title)

            if phone_details is None:
                continue

            product['producer'] = phone_details[0]
            product['model'] = phone_details[1]
            product['title'] = title
            product['price'] = price
            product['url'] = url
            product['availability'] = availability

            yield product

        next_page = response.xpath(VexioXPaths.NEXT_PAGE).get()
        if next_page:
            yield response.follow(get_proxy_url(next_page), callback=self.parse)
            # yield response.follow(next_page,callback=self.parse)
