import requests
from lxml import etree
import os
import re
import time
from loguru import logger as log
import threading
import sys


class spider(threading.Thread):
    homeUrl = 'https://www.wshm23.com/'
    homeHtml = ''
    index = 0
    basePathUrl = 'https://img.pic-server.com/'
    serviceIndex = 0
    def __init__(self,fileUrl,update= False,itemNames={},isSaveHtml = False):
        threading.Thread.__init__(self)
        self.homeUrl = fileUrl
        self.update = update
        self.updateItemNames = itemNames
        self.isSaveHtml = isSaveHtml
    def downHtml(self,url = homeUrl,path = 'temp/',filename = 'home.html'):
        html = ''

        if os.path.exists(path + filename) and not self.update:
            with open(path + filename,'r') as ff:
                html = ff.read()
            log.debug('had down html\n')
        else:
            html = requests.get(url).text
            if self.isSaveHtml:
                with open(path + filename,'w') as ff:
                    ff.write(html)
            log.debug('down now html\n')
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

    #https://img.pic-server.com/[0]/2022-11-14/717/139/1.jpg
    def getNowItemLink(self,index):
        itemHtml = self.downHtml(self.homeUrl + self.imgItemLinkList[index],'temp/',self.itemname +"_" + str(index + 1) +"_item.html")
        itemHtml = etree.HTML(itemHtml)
        try:
            jpgOriginUrl = itemHtml.xpath('//div[@class="playerall"]/img/@src')[0]
        except:
            log.info("会员章节开始:{0}",index + 1)
            jpgOriginUrl = itemHtml.xpath('//img/@src')[0]
        jpgModuleUrl = re.split(r'[/]',jpgOriginUrl)
        self.jgpsuf =  re.split(r'\.',jpgOriginUrl)[-1]
        log.info(jpgModuleUrl)
        return jpgModuleUrl

    def combinationImageUrl(self,index,update = True):
        self.curItem = index - 1

        if update == False or self.serviceIndex == 0:
            jpgModuleUrl = self.getNowItemLink(self.curItem)
            self.baseImgUrl = self.basePathUrl + jpgModuleUrl[3] + '/'
            if len(jpgModuleUrl) == 8:
                #https://img.pic-server.com/[0]/2022-11-14/717/139/1.jpg
                self.templeImgUrl = self.baseImgUrl + jpgModuleUrl[4]+ '/' + jpgModuleUrl[5] + '/'
            if len(jpgModuleUrl) == 7:
                self.templeImgUrl = self.baseImgUrl + jpgModuleUrl[4]+ '/'
                #https://img.pic-server.com/2022-11-14/717/139/1.jpg
            if len(jpgModuleUrl) == 6:
                #https://img.pic-server.com/社团学姐/1/1.jpg
                self.templeImgUrl = self.baseImgUrl
            try:
                self.serviceIndex = int(jpgModuleUrl[-2])
            except:
                log.error("jpgModuleUrl[-2] = {0}",jpgModuleUrl[-2])
        else:
            self.serviceIndex += 1

        if not os.path.exists('static/images/' + self.itemname + '/' + str(index)):
            os.mkdir('static/images/' + self.itemname + '/' + str(index))
        url = self.templeImgUrl + str(self.serviceIndex) + '/'
        return url

    def getDownCurIndexByFile(self):
        dirList = os.listdir('static/images/' + self.itemname)
        #find last empty dir file
        lastIndex = 0
        for dirFile in dirList:
            if len(os.listdir('static/images/' + self.itemname + '/' + dirFile)) < 10:
                lastIndex = int(dirFile)
                break
            else:
                lastIndex += 1
        return lastIndex

    def downItemImage(self):
        self.imgInfo = {}
        self.imgItemLen = len(self.imgItemLinkList)
        try:
            if not os.path.exists('static/images/' + self.itemname):
                os.mkdir('static/images/' + self.itemname)
            try:
                lastIndex = self.updateItemNames[self.itemname]
            except:
                lastIndex = self.getDownCurIndexByFile()
            log.info("lasterIndex = {0},all dir file = {1}",lastIndex,self.imgItemLen)
            for i in range(lastIndex,self.imgItemLen):
                second_catalogue = self.combinationImageUrl(i)
                index = 1
                reCount = 0
                while True and reCount < 3:
                    time.sleep(0.1)
                    imgUrl = second_catalogue + str(index) + '.' + self.jgpsuf
                    rpy = self.downImage(imgUrl,str(index),'images/' + self.itemname +'/' + str(i) + '/','.' + self.jgpsuf)
                    log.debug("down image {0},rpy:{1}",imgUrl,rpy)
                    if 200 != rpy:
                        if index == 1:
                            second_catalogue = self.combinationImageUrl(i,update = False)
                            reCount += 1
                            continue
                        else:
                            break
                    
                    index += 1
        except Exception as e:
            log.error(e.args)
            log.error(e.strerror)
            log.error(second_catalogue)
            log.error(imgUrl)
    def run(self):
        self.homeHtml = self.downHtml()
        self.getWeekHref()
        self.foreachHTML()
        self.getItemImageInfo()
        # self.downdpicImg()
        # self.downtitleList()
    # down dpic file
    def downdpicImg(self):
        for dpicSrc in self.weekdpicList:
            index = self.weekdpicList.index(dpicSrc)
            itemname = self.weeknameList[index]
            self.downImage(dpicSrc,itemname,'dpic/')
    def downtitleList(self):
        for itemurl in self.weekItemList:  
            index = self.weekItemList.index(itemurl)
            self.itemname = self.weeknameList[index]
            log.debug('find name:' + self.itemname)
            itemhtml = self.downHtml(self.homeUrl + itemurl,filename = self.itemname + ".html")
            itemhtml = etree.HTML(itemhtml)
            #get href info
            self.imgItemTitleList = itemhtml.xpath("//div[@class='stab_list']//li/a/text()")
            self.savaTitle(self.imgItemTitleList,self.itemname)    
    def getItemImageInfo(self):
        for itemurl in self.weekItemList:  
            index = self.weekItemList.index(itemurl)
            self.itemname = self.weeknameList[index]
            if len(sys.argv) == 2 and self.itemname != sys.argv[1]:
                continue
            if len(self.updateItemNames) != 0:
                names = self.updateItemNames.keys()
                if self.itemname not in names:
                    continue
            
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
        for dayUrl in self.weekUrlList:
            self.index = self.weekUrlList.index(dayUrl)
            filename = 'week' + str(self.index + 1) + ".html"
            weekhtml = self.downHtml(self.homeUrl + dayUrl,filename = filename)
            if weekhtml == '':
                log.error(self.homeUrl + dayUrl + " open False")
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
    thread1 = spider(homeURL,update = False,itemNames = {'姐姐爱做菜':14},isSaveHtml=False)
    thread1.start()
    thread1.join()
    log.info("退出主线程")
    # thread1 = spider(homeURL,0)
    # thread2 = spider(homeURL,1)
    # thread3 = spider(homeURL,2)
    # thread4 = spider(homeURL,3)
    # thread5 = spider(homeURL,4)
    # thread6 = spider(homeURL,5)
    # thread7 = spider(homeURL,6)
    # # 开启新线程
    # thread1.start()
    # thread2.start()
    # thread3.start()
    # thread4.start()
    # thread5.start()
    # thread6.start()
    # thread7.start()
    # thread1.join()
    # thread2.join()
    # thread3.join()
    # thread4.join()
    # thread5.join()
    # thread6.join()
    # thread7.join()