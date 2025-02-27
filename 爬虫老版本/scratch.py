import requests
r = requests.get("https://baidu.com") #获得页面内容
print(r.status_code) #状态码
print(r.encoding)# = 'utf-8' 猜测内容编码方式
print(r.apparent_encoding) # 分析编码方式
print(r.text) #打印内容
print(requests.head("https://baidu.com")) #爬取网页头
print(requests.post("https://baidu.com")) #向html提交post请求方式
print()
print()
print()
