from flask import Flask,render_template,redirect,request
from flask import url_for
from markupsafe import escape
import os
import re
from spider import spider

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

homeURL= 'https://www.wshm23.com/'

def downLoadItem(item,direct='week'):
    thread1 = spider(homeURL,update = False,itemNames = {item:0},isSaveHtml=False,direct=direct)
    thread1.start()
    thread1.join(1)
    
def downLoadcmd(cmd,direct='week'):
    thread1 = spider(homeURL,update = False,isSaveHtml=False,cmd=cmd,direct=direct)
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
    global historyList
    if request.method == 'POST': 
        bt_dpic = request.values.get('dpic')
        bt_title = request.values.get('title')
        bt_root = request.values.get('root')
        print(bt_dpic)
        print(bt_title)
        print(bt_root)
        for year in historyList:
            bt_year = request.values.get(year)
            if bt_year == year:
                print(bt_year)
                return year
        print(bt_dpic)
        print(bt_title)
        print(bt_root)
        
        if (bt_dpic == '更新dpic'):
            downLoadcmd(1,'week')
        if (bt_title == '更新title'):
            downLoadcmd(2,'week')
        if (bt_root == '更新主页面'):
            downLoadInit()
            
    return 'week'
@app.route('/',methods=['POST', 'GET'])
def rootHome():
    global historyList
    if len(historyList) == 0:
        historyList = downLoadInit()
    value = buttonExec(request)    
    readLocalFile(value)
    return render_template('index.html',name = 'wshm',movies=movies,historyList = historyList,direct =value )

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

@app.route('/wshm/<direct>/<item>')
def wshmItem(direct,item):
    readLocalTitle(direct,item)
    downLoadItem(item,direct)
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
    app.run(debug = True)
    globalUpdate = False


