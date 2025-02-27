import requests
from bs4 import BeautifulSoup
def getHTMLText(url):
    try:
        r = requests.get(url,timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup
    except:
        return "产生异常"
if __name__ == "__main__":
    url = "http://www.cs50.ly/favorites"
    print(getHTMLText(url))