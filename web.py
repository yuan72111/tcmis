import requests
from bs4 import BeautifulSoup

from flask import Flask,render_template,request,make_response, jsonify
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
    link += "<a href=/spidermovie>爬取電影更新時間,上傳到firestore</a><hr>"
    link += "<a href=/searchMovie>輸入片名關鍵字,可以查詢資料庫符合的電影</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"
    link += "<a href=/weather>查詢天氣</a><hr>"
    link += "<a href=/rate>本周新片進DB</a><hr>"
    return link

from flask import request # 記得要在檔案最上方 import request

@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req["queryResult"]["action"]
    msg =  req["queryResult"]["queryText"]
    info = "我是黃柏源設計的機器人,動作：" + action + "； 查詢內容：" + msg
    return make_response(jsonify({"fulfillmentText": info}))


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather")
def weather():
    # 1. 取得使用者搜尋的縣市 (預設為空字串，這樣一進網頁就不會先抓台中)
    city = request.args.get("city", "")
   
    # 2. 搜尋介面 (表單)
    R = """
    <form action="/weather" method="get">
        請輸入縣市：<input type="text" name="city" placeholder="例如：台北市">
        <input type="submit" value="查詢">
    </form>
    <hr>
    """
   
    # 3. 判斷：如果使用者有輸入東西才去抓 API
    if city:
        city = city.replace("台", "臺")
       
        # 提醒：Authorization 記得要換成你申請到的正確金鑰喔！
        auth_key = "rdec-key-123-45678-011121314"
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={auth_key}&format=JSON&locationName={city}"
       
        try:
            Data = requests.get(url, verify=False)
            JsonData = json.loads(Data.text)
           
            # 檢查 API 是否有抓到這個縣市的資料
            if JsonData["records"]["location"]:
                loc_name = JsonData["records"]["location"][0]["locationName"]
                Weather = JsonData["records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
                Rain = JsonData["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
               
                R += f"<h2>{loc_name} 最新天氣預報</h2>"
                R += f"天氣狀況：{Weather}<br>"
                R += f"降雨機率：{Rain}%"
            else:
                R += f"<b style='color:orange;'>找不到「{city}」的資料，請確認名稱是否正確。</b>"
               
        except Exception as e:
            R += f"<b style='color:red;'>連線失敗或 API 金鑰錯誤。</b>"
    else:
        # 如果沒輸入東西，就顯示歡迎文字
        R += "<h1>歡迎使用天氣預報系統 作者:黃柏源</h1>"
        R += "請在上方輸入框輸入想要查詢的縣市名稱。"

    return R

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月) 作者:黃柏源</h1>"
    
    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
    
    Data = requests.get(url)
    
    JsonData = json.loads(Data.text)
    
    for item in JsonData:
        R += f"{item['路口名稱']}, 原因: {item['主要肇因']}, 件數: {item['總件數']}<br>"
    
    return R

from flask import Flask, request

@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    if request.method == "POST":
        keyword = request.values.get("keyword")
        db = firestore.client()
        # 取得所有電影資料
        docs = db.collection("電影2B").get()

        R = f"<h3>關鍵字「{keyword}」的查詢結果：</h3><hr>"
        found = False

        for doc in docs:
            m = doc.to_dict()
            if keyword in m.get("title", ""):
                found = True
                # 取得編號(ID)與各項欄位
                R += f"<b>編號：</b>{doc.id}<br>"
                R += f"<b>片名：</b>{m.get('title')}<br>"
                R += f"<b>日期：</b>{m.get('showDate')}<br>"
                R += f"<a href='{m.get('hyperlink')}'>點我查看介紹</a><br>"
                R += f"<img src='{m.get('picture')}' width='150'><br><hr>"

        if not found:
            R += "查無符合條件的電影。"

        return R + "<a href='/searchMovie'>重新查詢</a> | <a href='/'>回首頁</a>"

    else:
        # 簡單的輸入畫面
        return """
            <h2>電影搜尋</h2>
            <form method="POST">
                請輸入關鍵字：<input type="text" name="keyword">
                <button type="submit">查詢</button>
            </form>
            <br><a href="/">回首頁</a>
        """

@app.route("/spidermovie")
def spidermovie():
    R = ""
    db = firestore.client()

    import requests
    from bs4 import BeautifulSoup
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間:", "")

    result=sp.select(".filmListAllX li")
    info = ""
    total = 0
    for item in result:
      total += 1
      movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
      title = item.find(class_="filmtitle").text
      picture = "https://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "https://www.atmovies.com.tw" + item.find("a").get("href")

      showDate = item.find(class_="runtime").text[5:15]


      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showDate,
          "lastUpdate": lastUpdate
      }

      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

    R += "網站最近更新日期:" + lastUpdate + "<br>"
    R += "總共爬取" + str(total) + "部電影到資料庫"

    return R

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