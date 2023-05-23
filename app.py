from flask import Flask,render_template,redirect,request
from flask import url_for
from markupsafe import escape
import os
import re
from spider import spider
import threading
from loguru import logger as log
app = Flask(__name__)


movies = {}


def readLocalFile(direct = 'week'):
    global movies
    movies = {}
    titlePath = 'static/title/' + direct
    try:
        titleFileNames = os.listdir(titlePath)
    except:
        downLoadcmd(2,direct)
        titleFileNames = os.listdir(titlePath)
    dpicPath = 'static/dpic/'+ direct
    try:
        dpicFileNames = os.listdir(dpicPath)
    except:
        downLoadcmd(1,direct)
        dpicFileNames = os.listdir(dpicPath)                
    for names in titleFileNames:
        name = re.split('\.',names)[0]
        movies[name] = name + ".png"
sg_items = []
def readLocalTitle(direct,name):
    global sg_items    
    with open('static/title/'+ direct +'/' + name + '.ini','r') as file:
        sg_items = file.readlines()

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
def readLocalImg(direct,name,num):
    global imgList
    path = 'static/images/' + direct + '/'+ name + "/" + num
    imgList = strsort(os.listdir(path))
    print(imgList)

homeURL= 'https://www.wshm.cc/'

downLoadItemDict = {"":""}
def downLoadItem(item,direct='week',index = 1):
    global downLoadItemDict
    log.info("begin down file {0}",item)
    thread1 = spider(homeURL,update = False,itemNames = {item:index},isSaveHtml=False,catalogue=direct)
    thread1.start()
    thread1.join(1)
    downLoadItemDict[item] = thread1
    
def downLoadcmd(cmd,direct='week'):
    thread1 = spider(homeURL,update = False,isSaveHtml=False,cmd=cmd,catalogue=direct)
    thread1.start()
    thread1.join(1)
    
globalUpdate = False
def downLoadInit():
    global globalUpdate
    thread1 = spider(homeURL,update = globalUpdate,isSaveHtml=True,cmd = 3)
    thread1.start()
    thread1.join(1)
    return thread1.yearNameList


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
            downLoadcmd(1,'week')
        elif (bt_name == '更新title'):
            downLoadcmd(2,'week')
        elif (bt_name == '更新主页面'):
            downLoadInit()
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
    if len(historyList) == 0:
        historyList = downLoadInit()
    value = buttonExec(request)
    if value == 'week':
        pass
    readLocalFile(value)
    return render_template('index.html',name = 'wshm',movies=movies,historyList = historyList,direct =value,downItemDict = downLoadItemDict )

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'

@app.route('/wshm/up/<direct>/<item>/<int:num>')
def page_up(direct,item,num):
    num = num - 1
    num = str(num)
    readLocalImg(direct,item,num)
    return render_template('showImg.html',name = item,num = num,imgList=imgList,direct=direct)

@app.route('/wshm/down/<direct>/<item>/<int:num>')
def page_down(direct,item,num):
    num = num + 1
    num = str(num)
    readLocalImg(direct,item,num)
    return render_template('showImg.html',name = item,num = num,imgList=imgList,direct=direct)



@app.route('/wshm/<direct>/<item>',methods=['POST', 'GET'])
def wshmItem(direct,item):
    readLocalTitle(direct,item)
    index = 1
    if request.method == 'POST': 
        name = list(request.values.keys())[0]
        log.debug("name:{0}",request.values.keys())
        bt_name = request.values.get(name)
        log.debug("btn:{0}",bt_name)
        if 'allupdate' in request.values.keys():
            downLoadItem(item,direct)
        if 'singupdate' in request.values.keys():
            index = request.form.get('index')
            downLoadItem(item,direct,int(index))
            
    log.info("index:{0},item:{1},direct:{2}",index,item,direct)
    return render_template('item.html',name = 'wshm',allItems = sg_items,item = item,direct=direct)

@app.route('/wshm/img/<direct>/<item>/<num>/<itemName>')
def wshmImgShow(direct,item,num,itemName):
    readLocalImg(direct,item,num)
    return render_template('showImg.html',direct = direct,name = item,num = num,imgList=imgList,itemName=itemName)


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


