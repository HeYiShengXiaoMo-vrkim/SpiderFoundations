# 从此处理api错误
import requests
#r = requests.get("https://www.amazon.cn/gp/product/B01M8L5Z3Y")
#r.encoding = r.apparent_encoding
#print(r.status_code)
#print(r.text) # 在这里打印出来访问错误，同时说明并不是网络错误
#print(r.request.headers) # 检查访问头的问题，发现user-agent是python的request，并不让爬取
kv = {'user-agent' : 'Mozilla/5.0'}
url = "https://www.amazon.cn/gp/product/B01M8L5Z3Y"
r = requests.get(url, headers=kv) #模拟浏览器更改访问头
print(r.status_code)
print(r.text)
print(r.request.headers)