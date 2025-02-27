import requests
from bs4 import BeautifulSoup
def getHTML(url):
    try:
        r = requests.get(url) #使用requests库的get获取网页内容
        r.encoding = r.apparent_encoding #更换网页的解码格式
        print(r.status_code) # 检查是否连接上该网站
        demo = r.text
        soup = BeautifulSoup(demo, "html.parser")
        return soup.prettify()# 返回网页内容
    except:
        return "爬取失败" #失败了就返回，网络连接有风险要加保险
"""
def refreshHTML(demo):
    try:
        soup = BeautifulSoup(demo,"html.parser")
        print(soup.head) # 获得head的信息
        print(soup.head.contents) #检查head下子节点的信息
        len(soup.body.contents) #获得body子节点个数
        print(soup.body.contents[1]) #获得第2个子节点的内容
        for child in soup.body.children:
            print(child)  #遍历儿子节点
        for child in soup.body.children:
            print(child)  #遍历子孙节点
    except:
        return"none"
"""

url = "https://zhuanlan.zhihu.com/p/700170839"
demo = getHTML(url)
#refreshHTML(demo)
print(demo)

# for tag in soup.find_all(True):
#        print(tag.name)
#        打印所有标签的名字