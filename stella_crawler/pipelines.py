# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

import csv
from scrapy.exceptions import DropItem
from pymongo import Connection


class ItemValidationPipeline(object):
    """Checks the data of each item to make sure it is valid.
    """
    def process_item(self, item, spider):
        if not item['price']:
            raise DropItem("Missing price in %s" % item)
        else:
            return item


class DuplicatesPipeline(object):
    """Removes duplicates based on their product id.
    """
    def __init__(self):
        self.duplicates = set()

    def process_item(self, item, spider):
        if item['item_id'] in self.duplicates:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.duplicates.add(item['item_id'])
            return item


class DatabasePipeline(object):
    """Outputs the items to a mongodb database.
    """
    def __init__(self):
        connection = Connection()
        db = connection['stella']
        self.collection = db['items']

    def process_item(self, item, spider):
        self.collection.insert(dict(item))
        return item
