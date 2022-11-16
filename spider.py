import requests
from lxml import etree
import os
from loguru import logger as log
class spider():
    homeUrl = ''
    homeHtml = ''
    def __init__(self,fileUrl):
        self.homeUrl = fileUrl
    def downHtml(self,url = homeUrl,path = '.',filename = 'home.html'):
        html = ''
        if os.path.exists(filename):
            with open(filename,'r') as ff:
                html = ff.read()
            log.info('had down html\n')
        else:
            html = requests.get(url).text
            with open(filename,'w') as ff:
                ff.write(html)
            log.info('down now html\n')
        return html
    def getItemImageInfo(self):
        for itemurl in self.weekItemList:
            pass
        #test
        itemurl = self.weekItemList[0]
        itemname = self.weeknameList[0]
        itemhtml = self.downHtml(self.homeUrl + itemurl,filename = itemname + ".html")
        itemhtml = etree.HTML(itemhtml)
    def foreachHTML(self):
        self.weekItemList = []
        self.weeknameList = []
        for url in self.weekUrlList:
            filename = 'week' + str(self.weekUrlList.index(url) + 1) + ".html"
            weekhtml = self.downHtml(self.homeUrl + url,filename = filename)
            if weekhtml == '':
                log.error(self.homeUrl + url + " open false")
            weekhtml = etree.HTML(weekhtml)
            weekitem = weekhtml.xpath('//div[@class="li_img"]/a/@href')
            weekname = weekhtml.xpath('//a[@class="alink"]/@title')
            self.weekItemList += weekitem
            self.weeknameList += weekname
        pass
    def getWeekHref(self):
        self.homeHtml = etree.HTML(self.homeHtml)
        self.weekUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[:7]
        self.yearUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[7:]
if __name__ == '__main__':
    spr = spider('https://www.wshm23.com/')
    spr.homeHtml = spr.downHtml()
    spr.getWeekHref()
    spr.foreachHTML()
    spr.getItemImageInfo()