""" 
The Shopbop.com spider. 
"""

import re

# Scrapy tools
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request

from stella_crawler.items import StellaCrawlerItem

# Globals
NA = "N/A"

class ShopbopSpider(BaseSpider):
    """The Shopbop spider class. This spider knows how to crawl shopbop.com
    only. 
    """
    name = "shopbop"
    allowed_domains = ["shopbop.com"]
#    start_urls = [
#        "http://www.shopbop.com/ci/3/lp/womens-clothing.html"
#        ]

    def start_requests(self):
        """Defines the initial request to start the spider from, and the callback
        function to use when it is returned. This is used instead of the 
        start_urls list to configure a custom callback function.
        @return: list of requests from which to start crawling
        """
        start = Request("http://www.shopbop.com/ci/3/lp/womens-clothing.html",
                        callback=self.parse_init)
        return [start]
 
    def parse_init(self, response):
        """Parses shopbop the first time around.
        @rtype: Generator (iterable)
        @return: Request object
        """
        hxs = HtmlXPathSelector(response)
        # Randomization here
        categories = hxs.select('//a[@class=" leftNavCategoryLink"]/@href').extract()
        ## FIXME: Using only one category for testing
        for url in categories[5:6]:
            self.log("Got category url %s to yield" % url)
            yield Request("http://www.shopbop.com"+url, callback=self.parse_category)

    def parse_category(self, response):
        """Parses subsequent category (garment) sites based on <li>'s with 
        a subcategoryLink class. Generates new requests with subcategories.
        @return: Request object iterable
        """
        hxs = HtmlXPathSelector(response)
        # Randomization here
        subcategories = hxs.select(
            '//li[@class="leftNavSubcategoryLi"]/a/@href').extract()

        # Some weird shopbop redirect for the subcategory. 
        if response.url.find('clothes-leggings') != -1: 
            subcategories = None
        elif response.url.find('clothing-vests') != -1:
            subcategories = None
        
        if subcategories:
            # Getting rid of 'all' subcategory to avoid duplicates
            subcategories[:] = filter(lambda s: s.find('-all-jeans') == -1, 
                                      subcategories)
            
            for url in subcategories:
                self.log("parse_category: yielding "+url+" as next subcategory")
                # Add the baseIndex=0 in here to be able to crawl in next method
                yield Request("http://www.shopbop.com"+url+"?baseIndex=0", 
                              callback=self.parse_subcategory)
        else: 
            self.log("parse_category: no subcategories found from "
                     +response.url)
            yield Request(response.url+"?baseIndex=0", 
                          callback=self.parse_subcategory)

    def parse_subcategory(self, response):
        """Parses the subcategory page, i.e. the page in which we will begin 
        to look at each item. First, we create responses for the following pages, 
        calling this method as callback. Second we parse the items themselves, 
        creating responses for the parse_item_page method.
        """
        hxs = HtmlXPathSelector(response)
        # Part 1: 'Next' links
        # manually tweak the url
        # In order to do this, we have to find the max # of clothes 
        # in this subcategory
        num_items = hxs.select(
            '//div[@class="paginationHolder"]/div/text()').extract()
        num_items = int(num_items[0].rstrip('items').rstrip())
        url = response.url

        # Sample = "http://www.shopbop.com/clothing-denim/br/v=1/2534374302064814.htm?baseIndex=0"
        curr_index_obj = re.search(r'[0-9]+$', url)
        if curr_index_obj: 
            curr_index = int(curr_index_obj.group(0))
        if curr_index > 0: # We are not at baseIndex=0 
            if curr_index < (num_items - 40):
                url = url[:-len(str(curr_index))] + str(curr_index + 40)
                self.log("REQUEST::SUB_INDEX_LINK: %s" % url)
                yield Request(url, callback=self.parse_subcategory)
        else: # we are at baseIndex=0
            if 0 < (num_items - 40):
                url = url[:-1] + "40"
                self.log("REQUEST::SUB_INDEX_LINK %s" % url)
                yield Request(url, callback=self.parse_subcategory)
                
        # Part 2: Items
        item_links = hxs.select(
            '//a[@class="productDetailLink"]/@href').extract()
        for url in item_links:
            self.log("REQUEST::ITEM_LINK: %s" % url)
            yield Request("http://www.shopbop.com"+url, 
                          callback=self.parse_item_page)

    def parse_item_page(self,response):
        """ Parses the item page to extract all item information into item 
        object.
        """
        # This brings up the scrapy shell per call for checking
        #inspect_response(response)
        hxs = HtmlXPathSelector(response)
        ## TODO: Place checks in case category_item is not available. --> Log it
        ### The check for a hxs return is []

        # First, do the global attributes
        item = StellaCrawlerItem()
        num_colors = 1
        colors = []
        
        # Get the colors
        while True:
            swatches_div = hxs.select('//div[@id="swatches"]')
            colors.append(swatches_div.select(
                    'img['+str(num_colors)+']/@title').extract()[0])
            # Check for more
            potential_color = swatches_div.select(
                'img['+str(num_colors+1)+']/@title').extract()
            if not potential_color: break
            num_colors += 1

        ## TODO: Why is this a list?
        item['image_urls'] = [hxs.select(
                '//div[@id="productZoomImage"]/@href').extract()[0]]
        # The Shopbop description box contains many elements.
        description_box = hxs.select('//div[@id="descriptionDiv"]/text()')
        # The breadcrumbs tell us which category, subcategory this item is from.
        category = hxs.select(
            '//div[@id="breadcrumbs"]/a[2]/text()').extract()[0]
        subcategory_maybe = hxs.select(
            '//div[@id="breadcrumbs"]/a[3]/text()').extract()
        subcategory = NA
        if subcategory_maybe:
            subcategory = subcategory_maybe[0]

        # Field population
        # Housekeeping
        item['num_colors'] = num_colors
        item['colors'] = colors
        # Not from description box
        item['category'] = category
        item['subcategory'] = subcategory
        item['brand'] = hxs.select(
            '//h1[@class="brandLink"]/a/text()').extract()[0]
        item['item_id'] = hxs.select(
            '//span[@id="productCode"]/text()').extract()[0]
        # if there is a sale, get original price
        price = hxs.select('//span[@class="originalRetailPrice"]/text()')
        if price: 
            price = price.extract()[0]
        else: 
            price = hxs.select(
            '//div[@class="priceBlock"]/text()').extract()[0].strip().rstrip()
        item['price'] = price[1:] # Removing the $ sign
        
        item['name'] = hxs.select(
            '//div[@id="productTitle"]/text()').extract()[0]
        
        # RE's from description box
        item['description'] = description_box.extract()[0].strip().rstrip()
        test_fabrication = description_box.re(
            r"""(?<=Fabrication: )([\w+\W?]+)""")
        if test_fabrication: 
            item['fabrication'] = test_fabrication[0]
        else: 
            item['fabrication'] = NA 
        item['fabric'] = description_box.re(r"""(\d{1,2}% \w+)+""")
        item['embellishment'] = NA
        item['print_style'] = NA

        return item
