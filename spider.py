import requests
from lxml import etree
import os
import re
import time
from loguru import logger as log
import threading


class spider(threading.Thread):
    homeUrl = ''
    homeHtml = ''
    index = 0
    basePathUrl = 'https://img.pic-server.com/'
    def __init__(self,fileUrl,index):
        threading.Thread.__init__(self)
        self.homeUrl = fileUrl
        self.index = index
    def downHtml(self,url = homeUrl,path = 'temp/',filename = 'home.html'):
        html = ''
        if os.path.exists(path + filename):
            with open(path + filename,'r') as ff:
                html = ff.read()
            log.info('had down html\n')
        else:
            html = requests.get(url).text
            with open(path + filename,'w') as ff:
                ff.write(html)
            log.info('down now html\n')
        return html
    def downImage(self,url,name,path,imgType = '.png'):
        if os.path.exists("static/" + path + name + imgType):
            log.info('image:{0} had down \n',name)
            return 200
        img = requests.get(url)
        if img.status_code != 200:
            return img.status_code
        with open("static/" + path +  name + imgType,'wb') as file:
             file.write(img.content)
        return img.status_code
    
    def savaTitle(self,listTitle,name,path = 'static/title/'):        
        with open(path+name+'.ini','w') as file:
            for title in listTitle:
                file.write(title + "\n")
    def downItemImage(self):
        imgInfo = {}
        imgItemLen = len(self.imgItemLinkList)
        itemHtml = self.downHtml(self.homeUrl + self.imgItemLinkList[0],'temp/',self.itemname + "_item.html")
        itemHtml = etree.HTML(itemHtml)
        jpgOriginUrl = itemHtml.xpath('//div[@class="playerall"]/img/@src')[0]

        #https://img.pic-server.com/[0]/2022-11-14/717/139/1.jpg
        try:
            jpgModuleUrl = re.split(r'[/]',jpgOriginUrl)
            jgpsuf =  re.split(r'\.',jpgOriginUrl)[-1]
            log.debug(jgpsuf)
            log.debug(jpgModuleUrl)
            if not os.path.exists('static/images/' + self.itemname):
                os.mkdir('static/images/' + self.itemname)
            baseImgUrl = self.basePathUrl + jpgModuleUrl[3] + '/'
            
            for i in range(1,imgItemLen):
                
                if not os.path.exists('static/images/' + self.itemname + '/' + str(i)):
                    os.mkdir('static/images/' + self.itemname + '/' + str(i))
                if len(jpgModuleUrl) == 8:
                    #https://img.pic-server.com/[0]/2022-11-14/717/139/1.jpg
                    templeImgUrl = baseImgUrl + jpgModuleUrl[4]+ '/' + jpgModuleUrl[5] + '/' + str(i) + '/'
                if len(jpgModuleUrl) == 7:
                    templeImgUrl = baseImgUrl + jpgModuleUrl[4]+ '/'+ str(i) + '/' 
                    #https://img.pic-server.com/2022-11-14/717/139/1.jpg
                if len(jpgModuleUrl) == 6:
                    #https://img.pic-server.com/社团学姐/1/1.jpg
                    templeImgUrl = baseImgUrl + str(i) + '/' 

                for index in range(1,100):
                    imgUrl = templeImgUrl + str(index) + '.' + jgpsuf
                    rpy = self.downImage(imgUrl,str(index),'images/' + self.itemname +'/' + str(i) + '/','.' + jgpsuf)
                    log.debug("down image " + imgUrl)
                    if 200 != rpy:
                        if index == 1:
                            itemHtml = self.downHtml(self.homeUrl + self.imgItemLinkList[i-1],'temp/',self.itemname + str(i) + "_item.html")
                            itemHtml = etree.HTML(itemHtml)
                            jpgOriginUrl = itemHtml.xpath('//div[@class="playerall"]/img/@src')[0]
                            jpgModuleUrl = re.split(r'[/]',jpgOriginUrl)
                            baseImgUrl = self.basePathUrl + jpgModuleUrl[3] + '/'
                            jgpsuf =  re.split(r'\.',jpgOriginUrl)[-1]
                            log.debug(jpgModuleUrl)
                            if len(jpgModuleUrl) == 8:
                                #https://img.pic-server.com/[0]/2022-11-14/717/139/1.jpg
                                templeImgUrl = baseImgUrl + jpgModuleUrl[4]+ '/' + jpgModuleUrl[5] + '/' + str(i) + '/'
                            if len(jpgModuleUrl) == 7:
                                templeImgUrl = baseImgUrl + jpgModuleUrl[4]+ '/'+ str(i) + '/' 
                                #https://img.pic-server.com/2022-11-14/717/139/1.jpg
                            if len(jpgModuleUrl) == 6:
                                #https://img.pic-server.com/社团学姐/1/1.jpg
                                templeImgUrl = baseImgUrl + str(i) + '/' 
                            continue
                        else:
                            break        
                    time.sleep(0.1)
        except:
            log.debug(jpgOriginUrl)
            log.debug(imgUrl)
    def run(self):
        self.homeHtml = self.downHtml()
        self.getWeekHref()
        self.foreachHTML()
        self.getItemImageInfo()
        # self.downdpicImg()
    # down dpic file
    def downdpicImg(self):
        for dpicSrc in self.weekdpicList:
            index = self.weekdpicList.index(dpicSrc)
            itemname = self.weeknameList[index]
            self.downImage(dpicSrc,itemname,'dpic/')
            
    def getItemImageInfo(self):
        for itemurl in self.weekItemList:  
            index = self.weekItemList.index(itemurl)
            self.itemname = self.weeknameList[index]
            log.debug('find name:' + self.itemname)
            itemhtml = self.downHtml(self.homeUrl + itemurl,filename = self.itemname + ".html")
            itemhtml = etree.HTML(itemhtml)
            #get href info
            self.imgItemLinkList = itemhtml.xpath("//div[@class='stab_list']//li/a/@href")
            self.imgItemTitleList = itemhtml.xpath("//div[@class='stab_list']//li/a/text()")
            self.savaTitle(self.imgItemTitleList,self.itemname)
            self.downItemImage()
     
    def foreachHTML(self):
        self.weekItemList = []
        self.weeknameList = []
        self.weekdpicList = []
        url = self.weekUrlList[self.index]
        filename = 'week' + str(self.index + 1) + ".html"
        weekhtml = self.downHtml(self.homeUrl + url,filename = filename)
        if weekhtml == '':
            log.error(self.homeUrl + url + " open false")
        weekhtml = etree.HTML(weekhtml)
        weekitem = weekhtml.xpath('//div[@class="li_img"]/a/@href')
        weekname = weekhtml.xpath('//a[@class="alink"]/@title')
        weekdpic = weekhtml.xpath('//img[@class="dpic dh"]/@src')
        self.weekItemList += weekitem
        self.weeknameList += weekname
        self.weekdpicList += weekdpic
        pass
    def getWeekHref(self):
        self.homeHtml = etree.HTML(self.homeHtml)
        self.weekUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[:7]
        self.yearUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[7:]
if __name__ == '__main__':
    homeURL= 'https://www.wshm23.com/'
    thread1 = spider(homeURL,0)
    thread2 = spider(homeURL,1)
    thread3 = spider(homeURL,2)
    thread4 = spider(homeURL,3)
    thread5 = spider(homeURL,4)
    thread6 = spider(homeURL,5)
    thread7 = spider(homeURL,6)
    # 开启新线程
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    thread5.start()
    thread6.start()
    thread7.start()
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()
    thread5.join()
    thread6.join()
    thread7.join()
    print ("退出主线程")
