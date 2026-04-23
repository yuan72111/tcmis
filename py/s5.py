import requests
from bs4 import BeautifulSoup

url = "http://127.0.0.1:5000/me"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("td iframe")
for item in result:
	print(item.get("src"))
