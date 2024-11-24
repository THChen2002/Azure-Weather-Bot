from config import Config
from api.linebot_helper import LineBotHelper
from flask import Flask, request, abort
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    LocationMessageContent
)
from linebot.v3.messaging import (
    TextMessage,
    FlexMessage,
    FlexContainer
)
from datetime import datetime, timedelta
import json

app = Flask(__name__)

config = Config()
configuration = config.configuration
line_handler = config.handler
azureService = config.azureService
weatherService = config.weatherService

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(event=MessageEvent, message=LocationMessageContent)
def handle_location_message(event):
    LineBotHelper.show_loading_animation(event)
    address = event.message.address
    messages = extract_address(address)
    LineBotHelper.reply_message(event, messages)

@line_handler.add(event=MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    LineBotHelper.show_loading_animation(event)
    user_msg = event.message.text
    messages = extract_address(user_msg)
    LineBotHelper.reply_message(event, messages)

def extract_address(text):
    result = azureService.analyze_address(text)
    entities = result['prediction']['entities']

    messages = []
    if len(entities) == 2 and entities[0]['category'] == 'city' and entities[1]['category'] == 'town':
        city = result['prediction']['entities'][0]['text']
        town = result['prediction']['entities'][1]['text']
        messages.append(TextMessage(text=f"你傳送的位址資訊的城市:{city}"))
        messages.append(TextMessage(text=f"你傳送的位址資訊的鄉鎮:{town}"))
        weather_data = weatherService.get_12hr_forecast(city, town)
        # weather_data = weatherService.get_12hr_forecast("臺北市", "大安區")
        astronomical_data = weatherService.get_astronomical_time("臺北市")
        line_flex_str = get_weather_flex(request, weather_data, astronomical_data, city, town)
        messages.append(FlexMessage(alt_text="建議穿搭", contents=FlexContainer.from_json(line_flex_str)))
    else:
        messages.append(TextMessage(text="無法辨識你傳送的位址資訊"))
    return messages


def get_weather_flex(request, weather_data, astronomical_data, city, town):
    url_root = request.url_root.replace("http://", "https://")
    time_desc = weatherService.get_time_desc(weather_data["start_time"][0])
    cloth_text, cloth_icon, suggestion_text, suggestion_icon = weatherService.get_suggestions(url_root, weather_data, 0)
    wx_code = [wx for wx in weather_data["Wx_code"]]
    wx_desc = [desc for desc in weather_data["Wx_desc"]]
    min_temp = [min_t for min_t in weather_data["MinT"]]
    max_temp = [max_t for max_t in weather_data["MaxT"]]
    pop_12h = [pop for pop in weather_data["PoP12h"]]

    # 根據建議的數量，選擇Flex Message的內容
    if len(cloth_text) == 1:
        if len(suggestion_text) == 2:
            with open("./flex/suggestion_12.json", "r", encoding="utf-8") as f:
                line_flex_json = json.load(f)
                line_flex_str = json.dumps(line_flex_json)
            params = {
                "cloth_text": cloth_text[i],
                "cloth_icon": cloth_icon[i],
            }
            line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)
            for i in range(2):
                params = {
                    "suggestion_text": suggestion_text[i],
                    "suggestion_icon": suggestion_icon[i],
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)
        elif len(suggestion_text) == 3:
            with open("./flex/suggestion_13.json", "r", encoding="utf-8") as f:
                line_flex_json = json.load(f)
                line_flex_str = json.dumps(line_flex_json)
            params = {
                "cloth_text": cloth_text[i],
                "cloth_icon": cloth_icon[i],
            }
            line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)
            for i in range(3):
                params = {
                    "suggestion_text": suggestion_text[i],
                    "suggestion_icon": suggestion_icon[i]
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)
    elif len(cloth_text) == 2:
        if len(suggestion_text) == 2:
            with open("./flex/suggestion_22.json", "r", encoding="utf-8") as f:
                line_flex_json = json.load(f)
                line_flex_str = json.dumps(line_flex_json)
            for i in range(2):
                params = {
                    "cloth_text": cloth_text[i],
                    "cloth_icon": cloth_icon[i],
                    "suggestion_text": suggestion_text[i],
                    "suggestion_icon": suggestion_icon[i]
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)
        elif len(suggestion_text) == 3:
            with open("./flex/suggestion_23.json", "r", encoding="utf-8") as f:
                line_flex_json = json.load(f)
                line_flex_str = json.dumps(line_flex_json)
            for i in range(2):
                params = {
                    "cloth_text": cloth_text[i],
                    "cloth_icon": cloth_icon[i],
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)
            for i in range(3):
                params = {
                    "suggestion_text": suggestion_text[i],
                    "suggestion_icon": suggestion_icon[i]
                }
                line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)

    now = datetime.now()
    sunrise_time = astronomical_data["SunRiseTime"]
    sunset_time = astronomical_data["SunSetTime"]
    moonrise_time = astronomical_data["MoonRiseTime"]
    moonset_time = astronomical_data["MoonSetTime"]
    sunrise_time = astronomical_data["SunRiseTime"]

    # 將 HH:MM 字串轉換為 timedelta
    def time_to_timedelta(time_str):
        hours, minutes = map(int, time_str.split(":"))
        return timedelta(hours=hours, minutes=minutes)

    # 取得當前時間並轉換為 timedelta
    now = datetime.now()
    current_time = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

    # 將天文資料轉換為 timedelta
    sunrise_td = time_to_timedelta(sunrise_time)
    sunset_td = time_to_timedelta(sunset_time)
    moonrise_td = time_to_timedelta(moonrise_time)
    moonset_td = time_to_timedelta(moonset_time)

    if moonset_td < moonrise_td:
        moonset_td += timedelta(days=1)

    # 計算日照百分比
    if sunrise_td <= current_time <= sunset_td:
        sun_width = round(((current_time - sunrise_td) / (sunset_td - sunrise_td)) * 100)
    else:
        sun_width = 100

    # 計算月照百分比
    if moonrise_td <= current_time <= moonset_td:
        moon_width = round(((current_time - moonrise_td) / (moonset_td - moonrise_td)) * 100)
    else:
        moon_width = 100
    params = {
        "city": city,
        "town": town,
        "sunrise_time": sunrise_time,
        "sunset_time": sunset_time,
        "sun_width": sun_width,
        "moon_width": moon_width,
        "moonrise_time": moonrise_time,
        "moonset_time": moonset_time
    }
    line_flex_str = LineBotHelper.replace_variable(line_flex_str, params)

    # 依序替換三個時段的天氣資訊
    for i in range(3):
        params = {
            "time_desc": time_desc[i],
            "minT": min_temp[i],
            "maxT": max_temp[i],
            "PoP": pop_12h[i],
            "Wx_url": f"{url_root}static/weather_icons/day{wx_code[i]}.jpg",
            "Wx_desc": wx_desc[i],
        }
        if i != 0:
            cloth_text, cloth_icon, suggestion_text, suggestion_icon = weatherService.get_suggestions(url_root, weather_data, i)
            params["cloth"] = ', '.join(cloth_text)

        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1).replace('\n', '')

    return line_flex_str

if __name__ == "__main__":
        app.run()