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
import json
class spider(threading.Thread):
    homeUrl = 'https://www.wshm.cc/'
    homeHtml = ''
    index = 0
    basePathUrl = 'https://img.pic-server.com/'
    serviceIndex = 0
    today = date.today()    
    nowDate = today.strftime("_%d_%m_%Y")
    jsonRpy = {"item":[]}
    def __init__(self,fileUrl,update= False,itemNames={},isSaveHtml = False,cmd=0,catalogue='week'):
        threading.Thread.__init__(self)
        self.homeUrl = fileUrl
        self.update = update
        self.updateItemNames = itemNames
        self.isSaveHtml = isSaveHtml
        self.cmd = cmd
        self.catalogue = catalogue
        log.debug(self.nowDate)

    def downImage(self,url,name,path,imgType = '.jpg'):
        if os.path.exists( path + name + imgType):
            log.info('image:{0} had down \n',name)
            return 200
        else:
            if not os.path.exists(path):
                os.makedirs(path)
        img = requests.get(url)
        if img.status_code != 200:
            return img.status_code
        try:
            with open(path +  name + imgType,'wb') as file:
                file.write(img.content)
        except:
            log.error("write file error {0} {1}",path +  name + imgType,type(img.content))
        return img.status_code
    
    def savaTitle(self,listTitle,name,path = 'static/title/'):        
        with open(path+name+'.ini','w') as file:
            for title in listTitle:
                file.write(title + "\n")
    def savaUrl(self,listTitle,name,path = 'static/title/'):        
        with open(path+name+'.json','w') as file:
                file.write(listTitle + "\n")
    def saveImage(self,threadArgs):
        index = threadArgs['index']
        path = threadArgs['path']
        title = threadArgs['title']
        imagesurl = "https://cdn.ifs7gsd2f.com/" + threadArgs['imageslist'][index]
        self.downImage(imagesurl,str(index),path)
        log.debug("{0}--{1}:{2}",title,index,len(threadArgs['imageslist']))    
    def threadDownImage(self,args):
        index = args['index']
        cartoonInfo = args['dictJson'][index]
        if not os.path.exists('static/images/' + cartoonInfo['title']):
            os.mkdir('static/images/' + cartoonInfo['title'])
        itemJson = ''
        with open('static/url/' + cartoonInfo['title'] + '.json','r') as file:
            itemJson = json.loads(file.read())
        # log.warning()("begin down item--{0}:{1}",cartoonInfo['title'],len(itemJson['result']['list']))
        for curlist in itemJson['result']['list']:
            title = curlist['title']
            imageslist = curlist['imagelist'].split(',')
            log.debug("begin down images :{0}:{1}/{2}",cartoonInfo['title'],title,len(imageslist))
            
            threadArgs = {}
            threadArgs['imageslist'] = imageslist
            threadArgs['title'] = title
            threadArgs['path'] = 'static/images/' + cartoonInfo['title'] + "/" + title + '/'
            with ThreadPoolExecutor(len(imageslist)) as t2:    
                for j in range(0,len(imageslist)):
                    threadArgs['index'] = j
                    t2.submit(self.saveImage, threadArgs)
            # i = 0
            # for image in imageslist:
            #     print(image)
            #     self.downImage("https://cdn.ifs7gsd2f.com/" + image,str(i),'static/images/' + cartoonInfo['title'] + "/" + title + '/')
            #     i += 1
        self.ImageDownCount += 1
        log.debug("{0}--{1}:{2}",index,cartoonInfo['title'],self.ImageDownCount)                       
        
    def downItemImage(self):
        if len(self.jsonRpy['item']) == 0:
            log.warning("not load json data")
            self.loadSaveJson()  
        try:
            threadArgs = {}
            threadArgs['dictJson'] = self.jsonRpy['item']
            self.ImageDownCount = 0
            maxThread = 20
            for i in range(0,len(self.jsonRpy['item']),maxThread):
                log.debug("begin down images {0}",i)
                with ThreadPoolExecutor(maxThread) as t2:    
                    for j in range(i,i + maxThread):
                        threadArgs['index'] = j
                        t2.submit(self.threadDownImage, threadArgs)
                while True:
                    if self.ImageDownCount == i + maxThread or self.ImageDownCount == len(self.jsonRpy['item']):
                        log.debug("had down a cycle:{0}",self.ImageDownCount)
                        break
        except Exception as e:
            log.error(e.args)
            log.error(e.strerror)
            log.error(second_catalogue)
            log.error(imgUrl)
    
    def downSignalImage(self,threadArgs):
        imagesInfo = threadArgs['imagedict']
        imageslist = imagesInfo['imagelist'].split(',')
        i = 0
        title = imagesInfo['title']
        itemName = self.updateItemNames['name']
        for image in imageslist:
            self.downImage("https://cdn.ifs7gsd2f.com/" + image,str(i),'static/images/' + itemName + "/" + title + '/')
            log.debug("{0}--{1}---{2}/{3}",itemName,title,i,len(imageslist))
            i += 1
        pass

    def downSignalItemImage(self):
        if len(self.jsonRpy['item']) == 0:
            log.warning("not load json data")
            self.loadSaveJson()                  
        threadArgs = {}
        itemJson = ''
        itemName = self.updateItemNames['name']
        itemIndex = self.updateItemNames['index']
        self.itemDownCount = 0
        for item in self.jsonRpy['item']:
            if itemName == item['title']:
                threadArgs['dictJson'] = item
                self.threadDownUrl(threadArgs)
        with open('static/url/' +  threadArgs['dictJson']['title'] + '.json','r') as file:
            itemJson = json.loads(file.read())['result']
        maxThread = int(itemJson['totalRow']) - itemIndex
    
        with ThreadPoolExecutor(maxThread) as t2:    
            for j in range(itemIndex,itemIndex + maxThread):
                threadArgs['imagedict'] = itemJson['list'][int(itemJson['totalRow']) - j]
                t2.submit(self.downSignalImage, threadArgs)
                
    def threadDownDpic(self,threadArgs):
        index = threadArgs['index']        
        cartoonInfo = threadArgs['dictJson'][index]
        # if not os.path.exists('static/dpic/' + cartoonInfo['title']):
        #     os.mkdir('static/dpic/' + cartoonInfo['title'])
        dpicSrc = "https://cdn.ifs7gsd2f.com" + cartoonInfo['image']
        rpy = self.downImage(dpicSrc,cartoonInfo['title'],'static/dpic/')
        self.dhcpDownCount += 1
        log.debug("{0}--{1}:{2}:{3}",index,cartoonInfo['title'],rpy,self.dhcpDownCount)
        pass
    def loadSaveJson(self):
        with open('static/item.json','r') as file:
            rpy = file.read()
            self.jsonRpy = json.loads(rpy)
    # down dpic file
    def downdpicImg(self):
        if len(self.jsonRpy['item']) == 0:
            log.warning("not load json data")
            self.loadSaveJson()            
        threadArgs = {}
        threadArgs['dictJson'] = self.jsonRpy['item']
        self.dhcpDownCount = 0
        for i in range(0,len(self.jsonRpy['item']),100):
            log.debug("begin down dpic {0}",i)
            with ThreadPoolExecutor(100) as t2:       
                for j in range(i,i + 100):
                    threadArgs['index'] = j
                    t2.submit(self.threadDownDpic, threadArgs)
            timeout = time.time()
            while True:
                if time.time() - timeout > 10:
                    log.debug("had down a cycle:{0},timeout",self.dhcpDownCount)
                    break
                if self.dhcpDownCount == i + 100 or self.dhcpDownCount == len(self.jsonRpy['item']):
                    log.debug("had down a cycle:{0}",self.dhcpDownCount)
                    break
    def saveTitleForJson(self,jsondata,title):
        rpy = json.loads(jsondata)
        listTitle = []
        for i in rpy['result']['list']:
            listTitle.append(i['title'])
        self.savaTitle(listTitle,title)
    def threadDownUrl(self,threadArgs):
    
        cartoonInfo = threadArgs['dictJson']
        log.debug("id = {0}",cartoonInfo['id'])
        dpicSrc = "https://www.a4d26.com/home/api/chapter_list/tp/{0}-0-1-{1}".format(cartoonInfo['id'],'1')
        # log.info(dpicSrc)
        try:
            rpy = requests.get(dpicSrc).text        
        except:
            log.error("url mush charge {0}",dpicSrc)
            self.itemDownCount += 1
            return
        # log.info(rpy)
        itemLen = json.loads(rpy)['result']['totalRow']        
        dpicSrc = "https://www.a4d26.com/home/api/chapter_list/tp/{0}-0-1-{1}".format(cartoonInfo['id'],str(itemLen))
        rpy = requests.get(dpicSrc).text
        self.saveTitleForJson(rpy,cartoonInfo['title'])
        self.savaUrl(rpy,cartoonInfo['title'],'static/url/')        
        self.itemDownCount += 1
        log.debug("{0}:{1}",cartoonInfo['title'],self.itemDownCount)
        pass
# down url
    def downUrl(self):
        if len(self.jsonRpy['item']) == 0:
            log.warning("not load json data")
            self.loadSaveJson()          
        threadArgs = {}
        self.itemDownCount = 0
        for i in range(0,len(self.jsonRpy['item']),100):
            log.debug("begin down url {0}",i)
            with ThreadPoolExecutor(100) as t2:
                for j in range(i,i + 100):
                    try:
                        threadArgs['dictJson'] = self.jsonRpy['item'][j]
                    except:
                        break
                    t2.submit(self.threadDownUrl, threadArgs)
            while True:
                if self.itemDownCount == i + 100 or self.itemDownCount == len(self.jsonRpy['item']):
                    log.debug("had down a cycle:{0}",self.itemDownCount)
                    break
    def getAllItemJson(self):
        itemCurIndex = 1
        originHttp = 'https://www.a4d26.com/home/api/cate/tp/1-0-2-1-{0}'
        
        while True:
            nowhttp = originHttp.format(str(itemCurIndex))
            itemCurIndex += 1            
            log.debug(nowhttp)
            rpy = requests.get(nowhttp).text
            rpy = json.loads(rpy)    
            self.jsonRpy['item'] += rpy['result']['list']
            log.info(rpy['result']['lastPage'])
            if rpy['result']['lastPage'] == True:
                break
        log.info(len(self.jsonRpy['item']))
        with open('static/item.json','w') as ff:
            ff.write(json.dumps(self.jsonRpy))
        log.info("had down save item json :{0}",len(self.jsonRpy['item']))
            

    def run(self):
        if self.cmd == 0:
            self.getAllItemJson()
        if self.cmd == 1:
            self.downdpicImg()
        if self.cmd == 2:
            if len(self.updateItemNames) == 0:
                self.downItemImage()
            else:
                self.downSignalItemImage()
        if self.cmd == 3:
            self.downUrl()
        log.info("update&down finish")

# with open("temp/home_14_05_2023.html",'r') as file:
#     rpy = file.read()
#     rpy = json.loads(rpy)
#     print(len(rpy['result']['list']))
#     print(rpy['result']['list'][0])
    # print(len(rpy['result']['list']))
    # print(rpy['result']['list'][0])

# https://www.a8b77.com/home/api/chapter_list/tp/1251-0-1-30
# if __name__ == '__main__':
#     # homeURL= 'https://www.a8b77.com/home/api/cate/tp/1-0-2-1-2'
#     homeURL= 'https://www.a8b77.com/home/api/chapter_list/tp/1251-0-1-30'
#     thread1 = spider(homeURL,update = True,itemNames = {"name":'小巷裡的秘密 ',"index":10},isSaveHtml = True,cmd=2)
#     thread1.start()
#     thread1.join()
#     log.info("退出主线程")
