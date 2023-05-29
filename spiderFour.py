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
import opencc
class spider(threading.Thread):
    # homeUrl = 'http://www.a8b77.com/'
    homeHtml = ''
    index = 0
    basePathUrl = 'https://img.pic-server.com/'
    serviceIndex = 0
    today = date.today()    
    nowDate = today.strftime("_%d_%m_%Y")
    jsonRpy = {"item":[]}
    converter = opencc.OpenCC("t2s")
    downListInfo = {}
    def __init__(self,fileUrl,update= False,itemNames={},isSaveHtml = False,cmd=0,catalogue='week'):
        threading.Thread.__init__(self)
        self.homeUrl = fileUrl
        self.update = update
        self.updateItemNames = itemNames
        self.isSaveHtml = isSaveHtml
        self.cmd = cmd
        self.catalogue = catalogue
        self.getNewUrl()
        log.debug(self.nowDate)
    def getNewUrl(self):
        orihtml = requests.get(self.homeUrl).text
        oriUrl = orihtml.split('http://www.')
        self.nowHtml = 'http://www.' + oriUrl[1].split('/')[0]        
        log.debug(self.nowHtml)
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
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path+name+'.ini','w') as file:
            for title in listTitle:
                file.write(title + "\n")
    def savaUrl(self,listTitle,name,path = 'static/title/'):        
        if not os.path.exists(path):
            os.makedirs(path)
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
            self.downListInfo["info"][self.updateItemNames['name']] = len(self.jsonRpy['item'])
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
        imageUrl = threadArgs['imageUrl']
        index = threadArgs['index']
        title = threadArgs['title']
        itemName = self.updateItemNames['name']
        self.downImage("https://cdn.ifs7gsd2f.com/" + imageUrl,str(index),'static/images/' + itemName + "/" + title + '/')
        log.debug("{0}--{1}---{2}/{3}",itemName,title,index)
        self.itemDownCount +=1 

    def downSignalItemImage(self):
        if len(self.jsonRpy['item']) == 0:
            log.warning("not load json data")
            self.loadSaveJson()                  
        threadArgs = {}
        itemJson = ''
        itemName = self.updateItemNames['name']
        itemIndex = self.updateItemNames['index']
        self.itemDownCount = 0
        t2sTitle = itemName
        for item in self.jsonRpy['item']:
            # log.error(item['title'])
            if itemName in self.converter.convert(item['title']):
                threadArgs['dictJson'] = item
                self.threadDownUrl(threadArgs)
                t2sTitle = self.converter.convert(item['title'])
        with open('static/url/' +  t2sTitle + '.json','r') as file:
            itemJson = json.loads(file.read())['result']
        self.downListInfo["info"][self.updateItemNames['name']] = len(itemJson['list'])
        for curitem in itemJson['list'][::-1][itemIndex:]:
            maxThread = len(curitem['imagelist'].split(','))
            with ThreadPoolExecutor(maxThread) as t2:
                threadArgs['title'] = curitem['title']
                for imageUrl in curitem['imagelist'].split(','):
                    threadArgs['imageUrl'] = imageUrl
                    threadArgs['index'] = curitem['imagelist'].split(',').index(imageUrl)
                    log.debug("title:{0} index:{1}",threadArgs['title'],threadArgs['index'])                 
                    t2.submit(self.downSignalImage, threadArgs)
            timeout = time.time()
            while self.itemDownCount != maxThread and time.time() - timeout < 10:
                pass
            self.itemDownCount = 0
        
                
    def threadDownDpic(self,threadArgs):
        index = threadArgs['index']        
        cartoonInfo = threadArgs['dictJson'][index]
        # if not os.path.exists('static/dpic/' + cartoonInfo['title']):
        #     os.mkdir('static/dpic/' + cartoonInfo['title'])
        dpicSrc = "https://cdn.ifs7gsd2f.com" + cartoonInfo['image']
        
        rpy = self.downImage(dpicSrc,self.converter.convert(cartoonInfo['title']),'static/dpic/')
        self.dhcpDownCount += 1
        log.debug("{0}--{1}:{2}:{3}",index,self.converter.convert(cartoonInfo['title']),rpy,self.dhcpDownCount)
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
        dpicSrc = self.nowHtml + "/home/api/chapter_list/tp/{0}-0-1-{1}".format(cartoonInfo['id'],'1')
        try:
            rpy = requests.get(dpicSrc).text        
        except:
            log.error("url mush charge {0}",dpicSrc)
            self.itemDownCount += 1
            return
        # log.info(rpy)
        itemLen = json.loads(rpy)['result']['totalRow']        
        dpicSrc = self.nowHtml + "/home/api/chapter_list/tp/{0}-0-1-{1}".format(cartoonInfo['id'],str(itemLen))
        rpy = requests.get(dpicSrc).text
        cartoonInfo['title']
        try:
            simplified_text  = self.converter.convert(cartoonInfo['title'])
        except:
            simplified_text  = cartoonInfo['title']
            log.warning("t2s convert false {0}",simplified_text)
        self.saveTitleForJson(rpy,simplified_text)
        self.savaUrl(rpy,simplified_text,'static/url/')
        self.itemDownCount += 1
        log.debug("{0}:{1}",simplified_text,self.itemDownCount)
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
            timeout = time.time()
            while True:
                if self.itemDownCount == i + 100 or self.itemDownCount == len(self.jsonRpy['item']):
                    log.debug("had down a cycle:{0}",self.itemDownCount)
                    break
                if time.time() - timeout > 10:
                    log.warning("had down a cycle timeout")
                    break
    def getAllItemJson(self):
        itemCurIndex = 1
        originHttp = self.nowHtml + '/home/api/cate/tp/1-0-2-1-{0}'
        
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
        directory = os.path.dirname("static/item.json")
        if not os.path.exists(directory):
            os.makedirs(directory)        
        with open('static/item.json','w') as ff:
            ff.write(json.dumps(self.jsonRpy))
        log.info("had down save item json :{0}",len(self.jsonRpy['item']))
            
    def hadDownImageList(self):
        directory = os.path.dirname("static/downList.json")
        if not os.path.exists(directory):
            os.makedirs(directory)  
        try:
            log.info(self.downListInfo["info"])
        except:
            if not os.path.exists('static/downList.json'):
                self.downListInfo = {"info":{self.updateItemNames['name']:0}}
            else:
                with open('static/downList.json','r') as file:
                    rpy = file.read()            
                    self.downListInfo = json.loads(rpy)
                    self.downListInfo["info"][self.updateItemNames['name']] = 0
        
        with open('static/downList.json','w') as ff:
            ff.write(json.dumps(self.downListInfo))
    def run(self):
        if self.cmd == 0:
            self.getAllItemJson()
        if self.cmd == 1:
            self.downdpicImg()
        if self.cmd == 2:
            self.hadDownImageList()
            if self.updateItemNames["index"] == -1:
                self.downItemImage()
            else:
                self.downSignalItemImage()
            self.hadDownImageList()
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
if __name__ == '__main__':
    homeURL= 'http://www.a8b77.com/'
    thread1 = spider(homeURL,update = True,itemNames = {"name":'高跟鞋',"index":20},isSaveHtml = True,cmd=2)
    thread1.start()
    thread1.join()
    log.info("退出主线程")
