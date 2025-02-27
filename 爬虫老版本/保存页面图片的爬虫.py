import requests
import os
path = "D:/abc.png"
url = "http://ultravioletbat.deviantart.com/art/Yay-Evil-111710573"
root = "D://pics//"
path = root + url.split('/')[-1] # 裁剪得到最后的JPG文件
try:
    if not os.path.exists(root):
        os.mkdir(root) #如果根目录并不存在创建一个
    if not os.path.exists(path):
        r = requests.get(url) #如果文件不存在进行文件获取
        with open(path,'wb') as f:
            f.write(r.content)
            f.close()
            print("文件保存成功")
    else:
        print("文件已存在")
except:
    print("爬取失败")
