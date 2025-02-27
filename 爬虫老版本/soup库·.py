import requests
r = requests.get("https://ambr.top/en")
demo = r.text
#print(demo)
from bs4 import BeautifulSoup
kv = {'user-agent' : 'Mozilla/5.0'}
r = requests.get("https://ambr.top/en", headers=kv)
print(r.status_code)
soup = BeautifulSoup(demo, "html.parser")
print(soup.prettify())
print(soup.name)
print(soup.name)
print(soup.name.a.parent.name)
tag = soup.a #获取soup中的一个a标签
tag.attrs #获取soup中的一个a标签内容
tag.attrs['class'] # 获得class标签的内容
type(tag) #得到tag标签的类型
