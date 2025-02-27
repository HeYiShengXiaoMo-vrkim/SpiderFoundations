
import requests
from bs4 import BeautifulSoup
import re
# 商品价格所在的位置在键值对view_price商品名字在raw_title
def get_html(url):
    try:
        response = requests.get(url,timeout=30)
        response.raise_for_status()
        response.encoding=response.apparent_encoding
        return response.text
    except:
        return " "
def parsePage(ilt, html):
    try:
        # ply为列表类型 反斜杠表示引入双引号，冒号，获得\d和*后的内容
        plt = re.findall(r'\"view_price\"\:\"[\d\.]*\"',html)
        # 获得商品名称信息
        tlt = re.findall(r'\"raw_title\"\:\".*?\"', html)
        for i in range(len(plt)):
            price = eval(plt[i].split(':')[1])
            title = eval(tlt[i].split(':')[1])
            ilt.append([price,title])
    except:
        print(" ")

def printGoodsList(ilt):
    tplt = "{:4}\t{:8}\t{:16}"
    print(tplt.format("序号", "价格", "商品名称"))
    count = 0 #输出计数器
    for g in ilt:
        count += 1
        print(tplt.format(count, g[0], g[1]))

def main():
    goods = "电竞椅"
    depth = 2 #爬多少页
    url = 'https://s.taobao.com/search?q=' + goods
    infoList = []
    for i in range(depth):
        try: #每一页都有不同的url，对每个url进行单独的访问
            url1 = url + '&s=' + str(44*i) #44*i指的是每个页面的商品数为44
            html = get_html(url1)
            parsePage(infoList, html)
        except:
            continue
    printGoodsList(infoList)

main()
