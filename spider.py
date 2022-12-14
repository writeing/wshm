import requests
from lxml import etree
import os
import re
import time
from loguru import logger as log
import threading
import sys
from concurrent.futures import ThreadPoolExecutor

class spider(threading.Thread):
    homeUrl = 'https://www.wshm23.com/'
    homeHtml = ''
    index = 0
    basePathUrl = 'https://img.pic-server.com/'
    serviceIndex = 0
    
    def __init__(self,fileUrl,update= False,itemNames={},isSaveHtml = False,cmd=0,direct='week'):
        threading.Thread.__init__(self)
        self.homeUrl = fileUrl
        self.update = update
        self.updateItemNames = itemNames
        self.isSaveHtml = isSaveHtml
        self.cmd = cmd
        self.direct = direct
        self.homeHtml = self.downHtml()
        self.getWeekHref()
        self.foreachWeekHTML()
        self.foreachYearHTML()
        
    def downHtml(self,url = homeUrl,path = 'temp/',filename = 'home.html'):
        html = ''
        if os.path.exists(path + filename) and not self.update:
            with open(path + filename,'r') as ff:
                html = ff.read()
            log.debug('had down html {0}\n',filename)
        else:
            html = requests.get(url).text
            if self.isSaveHtml:
                with open(path + filename,'w') as ff:
                    ff.write(html)
            log.debug('down now html {0}\n',filename)
        return html
    def downImage(self,url,name,path,imgType = '.png'):
        if os.path.exists( path + name + imgType):
            log.info('image:{0} had down \n',name)
            return 200
        img = requests.get(url)
        if img.status_code != 200:
            return img.status_code
        with open(path +  name + imgType,'wb') as file:
             file.write(img.content)
        return img.status_code
    
    def savaTitle(self,listTitle,name,path = 'static/title/'):        
        with open(path+name+'.ini','w') as file:
            for title in listTitle:
                file.write(title + "\n")

    #https://img.pic-server.com/[0]/2022-11-14/717/139/1.jpg
    def getNowItemLink(self,index):
        itemHtml = self.downHtml(self.homeUrl + self.imgItemLinkList[index],'temp/',str(index + 1) +"_item.html")
        itemHtml = etree.HTML(itemHtml)
        try:
            jpgOriginUrl = itemHtml.xpath('//div[@class="playerall"]/img/@src')[0]
        except:
            log.info("??????????????????:{0}",index + 1)
            jpgOriginUrl = itemHtml.xpath('//img/@src')[0]
        jpgModuleUrl = re.split(r'[/]',jpgOriginUrl)
        self.jgpsuf =  re.split(r'\.',jpgOriginUrl)[-1]
        log.info(jpgModuleUrl)
        return jpgModuleUrl

    def combinationImageUrl(self,index,path,update = True):
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
                #https://img.pic-server.com/????????????/1/1.jpg
                self.templeImgUrl = self.baseImgUrl
            try:
                self.serviceIndex = int(jpgModuleUrl[-2])
            except:
                log.error("jpgModuleUrl[-2] = {0}",jpgModuleUrl[-2])
        else:
            self.serviceIndex += 1  
                                
        if not os.path.exists(path + '/' + str(index)):
            os.mkdir(path + '/' + str(index))            
        url = self.templeImgUrl + str(self.serviceIndex) + '/'
        return url

    def getDownCurIndexByFile(self,path):
        dirList = os.listdir(path)
        #find last empty dir file
        lastIndex = 1
        for dirFile in dirList:
            if len(os.listdir(path + '/' + dirFile)) < 3:
                lastIndex = int(dirFile)
                break
            else:
                lastIndex += 1
        return lastIndex

    def threadDownImage(self,args):
        cartoonItemPath = args['path']
        i = args['index']
        second_catalogue = self.combinationImageUrl(i,cartoonItemPath)
        index = 1
        reCount = 0
        while True and reCount < 3:
            time.sleep(0.1)
            imgUrl = second_catalogue + str(index) + '.' + self.jgpsuf
            rpy = self.downImage(imgUrl,str(index),cartoonItemPath +'/' + str(i) + '/','.' + self.jgpsuf)
            log.debug("down image {0},rpy:{1}",imgUrl,rpy)
            if 200 != rpy:
                if index == 1:
                    second_catalogue = self.combinationImageUrl(i,cartoonItemPath,update = False)
                    reCount += 1
                    continue
                else:
                    break                    
            index += 1
        
    def downItemImage(self,itemname):
        self.imgInfo = {}
        self.imgItemLen = len(self.imgItemLinkList)
        try:
            cartoonItemPath = 'static/images/' + self.direct + '/' + itemname
            log.debug(cartoonItemPath)
            if not os.path.exists(cartoonItemPath):
                os.makedirs(cartoonItemPath)  
            try:
                lastIndex = self.updateItemNames[itemname]
                if lastIndex == 0:
                    lastIndex = self.getDownCurIndexByFile(cartoonItemPath)    
            except:
                lastIndex = self.getDownCurIndexByFile(cartoonItemPath)
            log.info("lasterIndex = {0},all dir file = {1}",lastIndex,self.imgItemLen)
            threadArgs = {}
            threadArgs['path'] = cartoonItemPath         
            with ThreadPoolExecutor(self.imgItemLen - lastIndex + 1) as t2:              
                for i in range(lastIndex,self.imgItemLen+1):
                    threadArgs['index'] = i
                    time.sleep(0.1)
                    t2.submit(self.threadDownImage, threadArgs)        

        except Exception as e:
            log.error(e.args)
            log.error(e.strerror)
            log.error(second_catalogue)
            log.error(imgUrl)
    # down dpic file
    def downdpicImg(self):
        if not os.path.exists('static/dpic/' + self.direct):
            os.mkdir('static/dpic/' + self.direct)
        cartoonInfo = self.carToonInfoDict[self.direct]
        for dpicSrc in cartoonInfo['dpic']:
            index = cartoonInfo['dpic'].index(dpicSrc)
            itemname = cartoonInfo['name'][index]                
            rpy = self.downImage(dpicSrc,itemname,'static/dpic/' + self.direct + '/')
            log.debug("{0}--{1}:{2}",itemname,dpicSrc,rpy)      
    def downtitleList(self):
        if not os.path.exists('static/title/' + self.direct):
            os.mkdir('static/title/' + self.direct)
        cartoonInfo = self.carToonInfoDict[self.direct]
        print(cartoonInfo)
        for itemurl in cartoonInfo['url']:
            index = cartoonInfo['url'].index(itemurl)
            itemname = cartoonInfo['name'][index]
            itemhtml = self.downHtml(self.homeUrl + itemurl,filename = itemname + ".html")
            itemhtml = etree.HTML(itemhtml)
            self.imgItemTitleList = itemhtml.xpath("//div[@class='stab_list']//li/a/text()")
            self.savaTitle(self.imgItemTitleList,itemname,path='static/title/' + self.direct + '/')
               
    def getItemImageInfo(self):
        cartoonInfo = self.carToonInfoDict[self.direct]
        for itemurl in cartoonInfo['url']:
            index = cartoonInfo['url'].index(itemurl)
            itemname = cartoonInfo['name'][index]
            if len(self.updateItemNames) != 0:
                names = self.updateItemNames.keys()
                if itemname not in names:
                    continue
            
            log.debug('find name:' + itemname)
            itemhtml = self.downHtml(self.homeUrl + itemurl,filename = itemname + ".html")
            itemhtml = etree.HTML(itemhtml)
            #get href info
            self.imgItemLinkList = itemhtml.xpath("//div[@class='stab_list']//li/a/@href")
            self.downItemImage(itemname)
     
    def foreachWeekHTML(self):
        self.carToonInfoDict = {}
        weekItemList = []
        weeknameList = []
        weekdpicList = []        
        for dayUrl in self.weekUrlList:    
            self.index = self.weekUrlList.index(dayUrl)
            filename = 'week' + str(self.index + 1) + ".html"
            weekhtml = self.downHtml(self.homeUrl + dayUrl,filename = filename)
            if weekhtml == '':
                log.error(self.homeUrl + dayUrl + " open False")
            weekhtml = etree.HTML(weekhtml)
            weekItemList += weekhtml.xpath('//div[@class="li_img"]/a/@href')
            weeknameList += weekhtml.xpath('//a[@class="alink"]/@title')
            weekdpicList += weekhtml.xpath('//img[@class="dpic dh"]/@src')
        self.carToonInfoDict['week'] = {'url':weekItemList,'name':weeknameList,'dpic':weekdpicList}
    def foreachYearHTML(self):
        for yearUrl in self.yearUrlList:
            self.index = self.yearUrlList.index(yearUrl)            
            downUrl = yearUrl
            curIndex = 1
            yearItemList = []
            yearnameList = []
            yeardpicList = []
            while True:
                filename = 'year_' + self.yearNameList[self.index] + '-' +str(curIndex) + ".html"
                yearhtml = self.downHtml(self.homeUrl + downUrl,filename = filename)
                if yearhtml == '':
                    log.error(self.homeUrl + downUrl + " open False")
                    break
                yearhtml = etree.HTML(yearhtml)
                yearItemList += yearhtml.xpath('//div[@class="li_img"]/a/@href')
                yearnameList += yearhtml.xpath('//a[@class="alink"]/@title')
                yeardpicList += yearhtml.xpath('//img[@class="dpic dh"]/@src')
                downUrl = yearhtml.xpath('//a/@href')[-3]
                downText = yearhtml.xpath('//a/text()')[-2]
                downUrl = downUrl[1:]
                if downText != r'??????':
                    self.carToonInfoDict[self.yearNameList[self.index]] = {'url':yearItemList,'name':yearnameList,'dpic':yeardpicList} 
                    break
                curIndex += 1
        pass
    def getWeekHref(self):
        self.homeHtml = etree.HTML(self.homeHtml)
        self.weekUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[:7]
        self.yearUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[7:]
        self.yearNameList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/text()')[7:]
    def run(self):
        if self.cmd == 0:
            self.getItemImageInfo()
        if self.cmd == 1:
            self.downdpicImg()
        if self.cmd == 2:
            self.downtitleList()
        
        log.info("update&down finish")
# if __name__ == '__main__':
#     homeURL= 'https://www.wshm23.com/'
#     thread1 = spider(homeURL,update = False,itemNames = {'???????????????':30},isSaveHtml=False)
#     thread1.start()
#     thread1.join()
#     log.info("???????????????")
