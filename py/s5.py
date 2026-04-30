import requests
from bs4 import BeautifulSoup
url = "http://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".filmListAllX li")
info = ""
for item in result:
  title = item.find(class_="filmtitle").text
  picture = "https://www.atmovies.com.tw" + item.find("img").get("src")

  info += title + "\n" + picture + "\n\n"
print(info)
