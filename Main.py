from typing import Iterable
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import re
import pandas as pd
import os
import json

# Define your spider
class MySpider(scrapy.Spider):
    name ='room'
    global list_items
    list_items = []
    def start_requests(self) :
        url = 'https://www.padsplit.com/api/auth/login'
        payload = {
            "email": "taylorajolly@gmail.com",
            "password": "6of*@@@nK^dzs"}
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'ajs_anonymous_id=655e640969ef481bab161b4fb6b83cfb; sessionid=q9g2opaddn6ns55uio0igklpe3mu3b1t'}
        yield scrapy.Request(
            url=url,
            method='POST',
            headers=headers,
            body=json.dumps(payload),  # Convert the dictionary to a JSON string
            callback=self.after_login)

    def after_login(self,response):
        url = 'https://www.padsplit.com/rooms-for-rent/austin-tx'
        # url = 'https://www.padsplit.com/rooms-for-rent/listing/tx/kyle/gorgeous-kyle-home-with-huge-rooms-and-backyard-amenities/4347?priceMin=50&priceMax=1000&noMoveInFee=false'
        yield scrapy.Request(url=url, callback=self.parse, meta={'url': url})
        
    def parse(self,response):
        rooms_boxes = response.xpath("//div[@class='MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12 MuiGrid-grid-md-6 MuiGrid-grid-xl-4 css-vg13d']//a[contains(@href,'rooms-for-rent')]")    
        for box in rooms_boxes:
            link = box.xpath(".//@href").get()
            yield scrapy.Request(url='https://www.padsplit.com'+link, callback=self.parse_rooms, meta={'url': link})
    
    def parse_rooms(self, response):
        url = response.meta.get('url')
        
        boxes = response.xpath('//div[@class="MuiGrid-root MuiGrid-container MuiGrid-spacing-xs-3 css-1h77wgb"]/div[@class="MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12 css-1au9qiw"]')
        json_text =  response.xpath('//script[@type="application/ld+json"]/text()').get()
        
        for box in boxes :
            item = {}
            item['url'] = 'https://www.padsplit.com'+url 
            item['Property Name'] = response.xpath('//h4/text()|//h1/text()').get()
            item['count_bathrooms'] = response.xpath('//div[@data-test-id="house-info__bathroom-txt"]/text()[1]').get()
            item['count_all_rooms']= response.xpath('//div[@data-test-id="house-info__bedroom-txt"]/text()').get(default = 0).replace('rooms','').replace('room','').strip()
            item['count_available_rooms']= response.xpath('//div[@id="__next"]//span[contains(text()," available")]/text()').get(default = 0).replace(' rooms available','').replace(' room available','').strip()
            item['count_filled_rooms']= int(item['count_all_rooms']) - int(item['count_available_rooms']) 
            item['Room Name'] = box.xpath('.//*[contains(@class,"typographyRoot bodyBold jss")]/text()').get()
            item['proporities'] = ' ,'.join(box.xpath('.//div[@class="MuiGrid-root MuiGrid-item css-1wxaqej"]//text()').getall())
            item['promotion'] = ''.join(box.xpath('.//div[@class="RoomCard_promoTag__hXUp_"]//div[@class="typographyRoot body"]/text()').getall())
            item['Price'] = box.xpath('.//div[@style="color:#128050" and contains(text(),"$")]/text()').get(default='')
            if item['Price'] == '':  item['Price'] = box.xpath('.//div[@style="color:#171717" and contains(text(),"$")]/text()').get()
            item['move_in_fees'] = ''.join(box.xpath('.//div[@class="typographyRoot bodyS" and contains(text(),"$")]/text()').getall())
            item['Features'] = ' ,'.join(response.xpath('//div[@class="MuiGrid-root MuiGrid-container ListingBlock_root___LjhI ListingBlock_withBorder__xMDZf ListingBlock_withAction___hGhi css-1d3bbye"]//div[@class="typographyRoot body"]/text()').getall())
            item['properity_id'] = ''.join(response.xpath('//span[@class="typographyRoot body"]/text()').getall())
            item['addressLocality'] = re.findall(r'"addressLocality":"(.*?)"',json_text)[0]
            item['addressRegion'] = re.findall(r'"addressRegion":"(.*?)"',json_text)[0]
            item['postalCode'] = re.findall(r'"postalCode":"(.*?)"',json_text)[0]
            item['latitude'] = re.findall(r'"latitude":"(.*?)"',json_text)[0]
            item['longitude'] = re.findall(r'"longitude":"(.*?)"',json_text)[0]
            item['room_images'] = ' , '.join(box.xpath('.//div[@class="RoomCard_galleryImage__QkBrx"]//span/img/@src').getall())
            print(item)
            list_items.append(item)
        df = pd.DataFrame(list_items)
        df.to_excel(os.path.join(os.getcwd(), "Temp_Output.xlsx"), index=False)
        
# Function to run the Scrapy spider in Jupyter
def run_spider(spider_class):
    settings = get_project_settings()
    settings.update({
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',  # Define the user agent
    'CONCURRENT_REQUESTS': 15,  # Set concurrent requests to 3
    'DOWNLOAD_DELAY': 0.2,  # Set delay between requests to 1 second
    'AUTOTHROTTLE_ENABLED': True,  # Enable AutoThrottle to adjust download rate automatically
    'AUTOTHROTTLE_START_DELAY': 1,  # The initial download delay for AutoThrottle
    'AUTOTHROTTLE_MAX_DELAY': 60,  # The maximum download delay for AutoThrottle
    'ROBOTSTXT_OBEY' : False,
    'LOG_LEVEL': 'CRITICAL',  # Set logging level to INFO (can be 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    })
    
    
    
    process = CrawlerProcess(settings)
    process.crawl(spider_class)
    process.start()

# Run the spider
run_spider(MySpider)
