# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class StellaCrawlerItem(Item):
    # All items have these fields
    brand = Field()
    price = Field()
    fabric = Field()
    color = Field()          # There may be more than one color
    num_colors = Field()
    length = Field()
    fabrication = Field()
    embellishment = Field()
    description = Field()
    name = Field()           # The name of the item
    print_style = Field()    # The print
    
    # Specific fields that only apply to certain items
    wash = Field()           # Denim
    rise = Field()           # Denim, Pants
    fit = Field()            # Denim 
    distressing = Field()    # Denim
    neckline = Field()       # Tops, dresses, sweaters
    sleeves = Field()
    guage_weight = Field()
    sheer_level = Field()
    lining = Field()
    waist_rise = Field()
    padding = Field()
    trim = Field()

    # These define the item's type
    category = Field()
    subcategory = Field()

    # The item's image(s)
    image_urls = Field()
