import requests
keyword = "Python"
try:
    kv = {'wd': 'python'}  #wd是百度搜索的端口号
    r = requests.get("https://www.baidu.com/s", params = kv)
    print(r.request.url)
    r.raise_for_status()
    print(len(r.text))
except:
    print("爬取失败")
