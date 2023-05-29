from flask import Flask,render_template,redirect,request
from flask import url_for
from markupsafe import escape
import os
import re
from spiderFour import spider
import threading
from loguru import logger as log
import json
app = Flask(__name__)


movies = {}
def readLocalFile(direct = ''):
    global movies
    movies = {}
    titlePath = 'static/title/'
    try:        
        titleFileNames = os.listdir(titlePath)
    except:
        downLoadcmd(2,direct)
        titleFileNames = os.listdir(titlePath)
    dpicPath = 'static/dpic/'
    try:
        dpicFileNames = os.listdir(dpicPath)
    except:
        downLoadcmd(1,direct)
        dpicFileNames = os.listdir(dpicPath)                
    for names in dpicFileNames:
        name = re.split('\.',names)[0]
        movies[name] = names
def readHadDownFile():
    global movies
    movies = {}
    ImagePath = 'static/downList.json'
    imageinfo = 1
    dpicPath = 'static/dpic/'
    dpicFileNames = os.listdir(dpicPath)
    with open(ImagePath,'r') as file:
        temp = file.read()        
        imageinfo = json.loads(temp)
    for imageitem in imageinfo["info"].keys():
        name = imageitem
        for oriName in dpicFileNames:
            if name in oriName: 
                movies[name] = oriName
    log.debug(movies)     
sg_items = []
def readLocalTitle(name):
    global sg_items
    titlePath = 'static/title/'
    titleFileNames = os.listdir(titlePath)
    for tt in titleFileNames:
        if name in tt:        
            with open('static/title/' + tt,'r') as file:
                sg_items = file.readlines()
def getFileName(item):
    dpicPath = 'static/dpic/'
    dpicFileNames = os.listdir(dpicPath)
    for tt in dpicFileNames:
      if item in tt:        
            return tt.split('.')[0]
def sort_key(s):
    # 排序关键字匹配
    # 匹配开头数字序号
    if s:
        try:
            c = re.findall('^\d+', s)[0]
        except:
            c = -1
        return int(c)

def strsort(alist):
    alist.sort(key=sort_key)
    return alist

imgList = []
def readLocalImg(name,itemName):
    global imgList
    imagesPath = 'static/images/'
    imagesFileNames = os.listdir(imagesPath)
    for tt in imagesFileNames:
        if name in tt:
            path = 'static/images/' + tt + "/" + itemName
            imgList = strsort(os.listdir(path))
            break
    print(imgList)

homeURL= ''

downLoadItemDict = {"":""}
def downLoadItem(item,index = -1):
    global downLoadItemDict
    log.info("begin down file {0} index:{1}",item,index)
    item = getFileName(item)
    thread1 = spider(homeURL,update = False,itemNames = {"name":item,"index":index},isSaveHtml=False,cmd=2)
    thread1.start()
    thread1.join(1)
    downLoadItemDict[item] = thread1
    
def downLoadcmd(cmd,direct='week'):
    thread1 = spider(homeURL,update = False,isSaveHtml=False,cmd=cmd)
    thread1.start()
    thread1.join(1)
    
globalUpdate = False
def downLoadInit():
    global globalUpdate
    thread1 = spider(homeURL,update = globalUpdate,isSaveHtml=True,cmd = 3)
    thread1.start()
    thread1.join(1)


historyList = []

def buttonExec(request):
    global historyList,downLoadItemDict
    if request.method == 'POST': 
        name = list(request.values.keys())[0]
        bt_name = request.values.get(name)
        for year in historyList:
            if bt_name == year:
                print(bt_name)
                return year
        
        if (bt_name == '更新dpic'):
            downLoadcmd(1) # updata dict
        elif (bt_name == '更新title'):
            downLoadcmd(0) # update all item
        elif (bt_name == '更新主页面'):
            downLoadInit()  # update all json            
        elif (bt_name == 'all'):
            readLocalFile()  # update all json  
        elif (bt_name == 'haddown'):
            readHadDownFile()  # update all json                          
        else:
            try:
                print(bt_name)
                print(downLoadItemDict)
                downLoadItemDict[bt_name].cancel()
            except:
                print("had cancel")
    return 'week'
@app.route('/',methods=['POST', 'GET'])
def rootHome():
    global historyList,downLoadItemDict
    if len(movies) == 0:
        readLocalFile('')
    buttonExec(request)
    return render_template('index.html',name = 'four',movies=movies,downItemDict = downLoadItemDict )

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'

@app.route('/wshm/up/<name>/<itemName>')
def page_up(name,itemName):
    if len(sg_items) == 0:
        readLocalTitle(name)    
    proitem = ' '
    for item in sg_items:        
        if itemName in item:         
           proitem = item   
           break
    if proitem != ' ' :
        index = sg_items.index(proitem)
        proitem = sg_items[index + 1].split('\n')[0] 
        readLocalImg(name,proitem)
    else:
        item = getFileName(name)
        ss = sg_items[::-1]
        return render_template('item.html',name = 'wshm',allItems = ss,item = item)
    log.debug(proitem)       
    return render_template('showImg.html',name = name,itemName = proitem,imgList=imgList)
@app.route('/wshm/page/<item>')
def page_page(item):
    if len(sg_items) == 0:
        readLocalTitle(item)
    item = getFileName(item)
    ss = sg_items[::-1]
    return render_template('item.html',name = 'wshm',allItems = ss,item = item)

@app.route('/wshm/down/<name>/<itemName>')
def page_down(name,itemName):
    if len(sg_items) == 0:
        readLocalTitle(name)
    proitem = sg_items[0]
    for item in sg_items:        
        if itemName in item:
            proitem = proitem.split('\n')[0]         
            readLocalImg(name,proitem)
            break
        proitem = item
    print(imgList)
    return render_template('showImg.html',name = name,itemName = proitem,imgList=imgList)



@app.route('/wshm/<item>',methods=['POST', 'GET'])
def wshmItem(item):
    item = item.split('.')[0]
    readLocalTitle(item)
    index = 1
    if request.method == 'POST': 
        name = list(request.values.keys())[0]
        log.debug("name:{0}",request.values.keys())
        bt_name = request.values.get(name)
        log.debug("btn:{0}",bt_name)
        if 'allupdate' in request.values.keys():
            downLoadItem(item)
        if 'singupdate' in request.values.keys():
            index = request.form.get('index')
            downLoadItem(item,int(index))
            
    log.info("index:{0},item:{1}",index,item)
    ss = sg_items[::-1]
    return render_template('item.html',name = 'wshm',allItems = ss,item = item)

@app.route('/wshm/img/<item>/<num>/<itemName>')
def wshmImgShow(item,num,itemName):
    readLocalImg(item,itemName)
    return render_template('showImg.html',name = item,num = num,imgList=imgList,itemName=itemName)


@app.route('/wshm/main')
def wshm_main():
    return redirect(url_for(test_url_for))

@app.route('/test')
def test_url_for():
    # 下面是一些调用示例（请访问 http://localhost:5000/test 后在命令行窗口查看输出的 URL）：
    print(url_for('rootHome'))  # 生成 hello 视图函数对应的 URL，将会输出：/
    # 注意下面两个调用是如何生成包含 URL 变量的 URL 的
    print(url_for('user_page', name='greyli'))  # 输出：/user/greyli
    print(url_for('user_page', name='peter'))  # 输出：/user/peter
    print(url_for('test_url_for'))  # 输出：/test
    # 下面这个调用传入了多余的关键字参数，它们会被作为查询字符串附加到 URL 后面。
    print(url_for('test_url_for', num=2))  # 输出：/test?num=2
    return 'Test page'

if __name__ == '__main__':
    app.run(debug=True)
    globalUpdate = False


