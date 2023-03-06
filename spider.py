import requests
from lxml import etree
import os
import re
import time
from loguru import logger as log
import threading
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta,datetime
class spider(threading.Thread):
    homeUrl = 'https://www.wshm.cc/'
    homeHtml = ''
    index = 0
    basePathUrl = 'https://img.pic-server.com/'
    serviceIndex = 0
    today = date.today()    
    nowDate = today.strftime("_%d_%m_%Y")
    def __init__(self,fileUrl,update= False,itemNames={},isSaveHtml = False,cmd=0,catalogue='week'):
        threading.Thread.__init__(self)
        self.homeUrl = fileUrl
        self.update = update
        self.updateItemNames = itemNames
        self.isSaveHtml = isSaveHtml
        self.cmd = cmd
        self.catalogue = catalogue
        self.homeHtml = self.downHtml(filename="home" + self.nowDate + ".html")
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
    def downImage(self,url,name,path,imgType = '.jpg'):
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
            temp = itemHtml.xpath('//div[@class="playerall"]/img/@src')[0]
            if len(temp) != 0:
              jpgOriginUrl = temp  
        except:
            log.error(self.imgItemLinkList[index] + "open false")
            exit(0)
        # except:
        #     temp = re.split(r'[/]',self.jpgOriginUrl)
        #     from_arg_dt  = temp[3]
        #     end_datetime = datetime.strptime(from_arg_dt, '%Y-%m-%d')
        #     for i in range(10):
        #         dt = end_datetime - timedelta(days=10-i)
        #         dt_str = dt.strftime('%Y-%m-%d')
        #         temp[3] = dt_str
        #         log.debug(temp)
        #         self.jpgOriginUrl = "".join(temp)
        #         rpy = self.downImage(self.jpgOriginUrl,temp[4] + temp[3],'temp/huiyuan')
        #         if rpy == 200:
        #             break
        #     log.error(self.jpgOriginUrl)    
        #     log.info("会员章节开始:{0} link:{1}",index + 1,self.jpgOriginUrl)            
        # jpgModuleUrl = re.split(r'[/]',self.jpgOriginUrl)
        # self.jgpsuf =  re.split(r'\.',self.jpgOriginUrl)[-1]
        # log.info(jpgModuleUrl)
        return jpgOriginUrl

    def combinationImageUrl(self,index,path,update = True):
        self.curItem = index - 1
        if update == False or self.serviceIndex == 0:
            jpgModuleUrl = self.getNowItemLink(self.curItem)
            self.baseImgUrl = self.basePathUrl + jpgModuleUrl[3] + '/'
            log.info(self.baseImgUrl)
            log.info(len(jpgModuleUrl))
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
                                
        if not os.path.exists(path + '/' + str(index)):
            os.mkdir(path + '/' + str(index))            
        url = self.templeImgUrl + str(self.serviceIndex) + '/'
        return url

    def getDownCurIndexByFile(self,path):
        dirList = os.listdir(path)
        #find last empty dir file
        lastIndex = 1
        for dirFile in dirList:
            if len(os.listdir(path + '/' + dirFile)) < 2:
                lastIndex = int(dirFile)
                break
            else:
                lastIndex += 1
        return lastIndex

    def threadDownImage(self,args):
        cartoonItemPath = args['path']
        i = args['index']
        #second_catalogue = self.combinationImageUrl(i,cartoonItemPath)
        second_catalogue = self.listDownUrl[i]
        index = 1
        reCount = 0    
        temp = re.split(r'[/]',second_catalogue)   
        while True and reCount < 3:
            time.sleep(0.1)
            temp[-1] = str(index) + '.jpg'
            imgUrl = "/".join(temp)
            rpy = self.downImage(imgUrl,str(index),cartoonItemPath +'/' + str(i) + '/',)
            log.debug("down {0},index:{1}/{2},rpy:{3}",cartoonItemPath,str(index),str(i),rpy)
            if 200 != rpy:
                if index == 1:
                    reCount += 1
                    continue
                else:
                    break                    
            index += 1
    def getCurItemDownUrl(self):
        self.listDownUrl = []
        originUrl = self.getNowItemLink(0)
        log.debug(originUrl)
        temp = re.split(r'[/]',originUrl)
        from_arg_dt  = temp[4]
        begin_datetime = datetime.strptime(from_arg_dt, '%Y-%m-%d')
        curIndex = 1
        temp[6] = str(curIndex)
        temp[-1] = '1.jpg'
        dateDay = 0
        errorCount = 0
        index3 = 0
        for i in range(self.imgItemLen * 8):      
            self.jpgOriginUrl = "/".join(temp)
            log.debug(self.jpgOriginUrl)
            img = requests.get(self.jpgOriginUrl)
            rpy = img.status_code
            if rpy == 200:
                self.listDownUrl.append(self.jpgOriginUrl)
                curIndex += 1
                temp[6] = str(curIndex)
                errorCount = 0
                continue
            elif temp[3] == '[3]':                  
                temp[3] = '[0]'
            else:
                temp[3] = '[3]'
                errorCount += 1
                if errorCount > 8:
                    errorCount = 0
                    dateDay -= 3
                    curIndex += 1
                    temp[6] = str(curIndex)
                dateDay += 1
                dt = begin_datetime + timedelta(days=dateDay)
                dt_str = dt.strftime('%Y-%m-%d')
                temp[4] = dt_str                    
        log.debug(self.listDownUrl)
    def downItemImage(self,itemname):
        self.imgInfo = {}
        self.imgItemLen = len(self.imgItemLinkList)
        try:
            cartoonItemPath = 'static/images/' + self.catalogue + '/' + itemname
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
            self.getCurItemDownUrl()
            with ThreadPoolExecutor(self.imgItemLen - lastIndex + 1) as t2:              
                for i in range(lastIndex,self.imgItemLen+1):
                    threadArgs['index'] = i
                    time.sleep(1)
                    t2.submit(self.threadDownImage, threadArgs)        

        except Exception as e:
            log.error(e.args)
            log.error(e.strerror)
            log.error(second_catalogue)
            log.error(imgUrl)
    def threadDownDpic(self,threadArgs):
        cartoonInfo = threadArgs['item']
        index = threadArgs['index']
        itemname = cartoonInfo['name'][index]       
        dpicSrc = cartoonInfo['dpic'][index]       
        rpy = self.downImage(dpicSrc,itemname,'static/dpic/' + self.catalogue + '/')
        log.debug("{0}--{1}:{2}",itemname,dpicSrc,rpy)    
        pass
    # down dpic file
    def downdpicImg(self):
        if not os.path.exists('static/dpic/' + self.catalogue):
            os.mkdir('static/dpic/' + self.catalogue)
        cartoonInfo = self.carToonInfoDict[self.catalogue]
        
        threadArgs = {}
        threadArgs['item'] = cartoonInfo
        with ThreadPoolExecutor(len(cartoonInfo['dpic'])) as t2:       
            for i in range(0,len(cartoonInfo['dpic'])):
                threadArgs['index'] = i
                time.sleep(0.1)
                t2.submit(self.threadDownDpic, threadArgs)
            
    def threadDownTitle(self,threadArgs):
        cartoonInfo = threadArgs['item']
        index = threadArgs['index']
        itemurl = cartoonInfo['url'][index]
        itemname = cartoonInfo['name'][index]
        itemhtml = self.downHtml(self.homeUrl + itemurl,filename = itemname + self.nowDate + ".html")
        itemhtml = etree.HTML(itemhtml)
        self.imgItemTitleList = itemhtml.xpath("//div[@class='stab_list']//li/a/text()")
        self.savaTitle(self.imgItemTitleList,itemname,path='static/title/' + self.catalogue + '/')
        pass
    def downtitleList(self):
        if not os.path.exists('static/title/' + self.catalogue):
            os.mkdir('static/title/' + self.catalogue)
        cartoonInfo = self.carToonInfoDict[self.catalogue]
        log.info(cartoonInfo['name'])
        log.info(len(cartoonInfo['name']))
        # for itemurl in cartoonInfo['url']:
        #     index = cartoonInfo['url'].index(itemurl)
        #     itemname = cartoonInfo['name'][index]
            
        threadArgs = {}
        threadArgs['item'] = cartoonInfo
        with ThreadPoolExecutor(len(cartoonInfo['url'])) as t2:       
            for i in range(0,len(cartoonInfo['url'])):
                threadArgs['index'] = i
                time.sleep(0.1)
                t2.submit(self.threadDownTitle, threadArgs)                    
    def getItemImageInfo(self):
        cartoonInfo = self.carToonInfoDict[self.catalogue]
        for itemurl in cartoonInfo['url']:
            index = cartoonInfo['url'].index(itemurl)
            itemname = cartoonInfo['name'][index]
            # if set update items
            if len(self.updateItemNames) != 0:
                names = self.updateItemNames.keys()
                if itemname not in names:
                    continue
            log.debug('find name:' + itemname)
            itemhtml = self.downHtml(self.homeUrl + itemurl,filename = itemname + self.nowDate + ".html")
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
            filename = 'week' + str(self.index + 1) + self.nowDate + ".html"
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
                if downText != r'下页':
                    self.carToonInfoDict[self.yearNameList[self.index]] = {'url':yearItemList,'name':yearnameList,'dpic':yeardpicList} 
                    break
                curIndex += 1
        pass
    def getWeekHref(self):
        self.homeHtml = etree.HTML(self.homeHtml)
        self.weekUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[:7]
        self.yearUrlList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/@href')[7:]
        self.yearNameList = self.homeHtml.xpath('//div[@class="nav_down clearfix"]/div[@class="nav_1000"]//li/a/text()')[7:]
        log.info(self.weekUrlList)
    def run(self):
        if self.cmd == 0:
            self.getItemImageInfo()
        if self.cmd == 1:
            self.downdpicImg()
        if self.cmd == 2:
            self.downtitleList()
        log.info("update&down finish")

if __name__ == '__main__':
    homeURL= 'https://www.wshm.cc/'
    thread1 = spider(homeURL,update = False,itemNames = {'小巷里的秘密':10},isSaveHtml = True,catalogue='week')
    thread1.start()
    thread1.join()
    log.info("退出主线程")
