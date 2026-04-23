import requests
from bs4 import BeautifulSoup

from flask import Flask,render_template,request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入黃柏源的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=黃柏源&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/math>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>讀取Firestore資料(根據姓名關鍵字:楊)</a><hr>"
    link += "<a href=/read3>讀取Firestore資料(根據姓名關鍵字:input)</a><hr>"
    link += "<a href=/spider1>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    return link

from flask import request # 記得要在檔案最上方 import request

@app.route("/movie1")
def movie1():
    # 1. 取得搜尋關鍵字
    q = request.args.get("q")
    
    # 2. 加上標題、搜尋介面 (讓使用者可以輸入)
    # 使用 <h1> 標記名稱，並建立一個 HTML 表單
    Result = "<h1>即將上映電影</h1>"
    Result += """
        <form action="/movie1" method="get">
            <input type="text" name="q" placeholder="請輸入片名關鍵字" value="{}">
            <button type="submit">搜尋</button>
        </form>
        <hr>
    """.format(q if q else "")
    
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    
    count = 0  # 用來計算符合條件的電影數量
    for item in result:
        title = item.find("img").get("alt")
        
        # 3. 搜尋邏輯：如果沒輸入關鍵字，或標題包含關鍵字才顯示
        if not q or q in title:
            count += 1
            introduce = "https://www.atmovies.com.tw" + item.find("a").get("href")
            Result += "<a href =" + introduce + ">" + title + "</a><br>"
            
            post = "https://www.atmovies.com.tw" + item.find("img").get("src")
            Result += "<img src =" + post + ">" + "</img><br><br>"
            
    # 如果有輸入關鍵字但沒找到任何電影
    if count == 0 and q:
        Result += "很抱歉，找不到包含「" + q + "」的電影。"
        
    return Result



@app.route("/spider1")
def spider1():
    Result = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        Result += i.text + i.get("href") + "<br>"
    return Result

from flask import Flask, request

@app.route("/read3")
def read3():
    keyword = request.args.get("keyword")
    
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.get()

    if not keyword:
        return """
        <h1>靜宜資管老師查詢</h1>
        <form action="/read3" method="get">
            請輸入老師姓名關鍵字：<input type="text" name="keyword">
            <button type="submit">查詢</button>
        </form>
        <br><a href="/">返回首頁</a>
        """

    for doc in docs:
        teacher = doc.to_dict()
        if keyword in teacher.get("name", ""):
            Result += str(teacher) + "<br>"

    if Result == "":
        Result = "抱歉，查無此關鍵字姓名之老師資料"
    
    return f"<h1>查詢結果</h1>{Result}<br><a href='/read3'>重新查詢</a>"

@app.route("/read2")
def read2():
    Result = ""
    keyword = "楊"
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.get()
    for doc in docs:    
        teacher = doc.to_dict()
        if keyword in teacher["name"]:
            Result += str(teacher) + "<br>"

    if Result == "":
        Result = "抱歉,查無此關鍵字姓名之老師資料"
    return Result
	
@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get()    
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"
    return Result


@app.route("/mis")
def course():
	return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():  
	now = datetime.now()
	return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():  
	return render_template("MIS2026B.html")
@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user,dep = d, cos= c)

@app.route("/math", methods=["GET", "POST"])
def math_calc():
    if request.method == "POST":
        try:
            x = float(request.form["x"])
            opt = request.form["opt"]
            y = float(request.form["y"])
           
            if opt == "^":
                result = x ** y
            elif opt == "√":
                if y == 0:
                    result = "錯誤：不能開0次方根"
                else:
                    result = x ** (1/y)
            else:
                result = "運算符號錯誤"
            return f"計算結果為：{result} <br><a href='/math'>回計算機</a>"
        except:
            return "請輸入正確的數字！<br><a href='/math'>返回</a>"
    else:
   
        return render_template("math.html")
        

if __name__ == "__main__":
	app.run(debug=True)