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
        weather_data = weatherService.get_12hr_forecast("臺北市", "大安區")
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
    line_flex_str = """{
        "type": "bubble",
        "size": "giga",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "icon",
                    "url": "https://cdn-icons-png.flaticon.com/512/3179/3179068.png"
                },
                {
                    "type": "text",
                    "text": "{{city}} {{town}}",
                    "weight": "bold",
                    "offsetStart": "sm"
                }
                ]
            },
            {
                "type": "text",
                "text": "{{time_desc}}",
                "weight": "bold",
                "margin": "md"
            },
            {
                "type": "text",
                "text": "{{minT}}° ~ {{maxT}}°",
                "size": "3xl",
                "weight": "bold",
                "margin": "none"
            },
            {
                "type": "box",
                "layout": "baseline",
                "contents": [
                {
                    "type": "icon",
                    "url": "https://cdn-icons-png.flaticon.com/512/46/46073.png"
                },
                {
                    "type": "text",
                    "text": "{{PoP}}%",
                    "size": "sm",
                    "offsetStart": "sm",
                    "flex": 1
                },
                {
                    "type": "text",
                    "text": "{{Wx_desc}}",
                    "size": "xs",
                    "weight": "bold",
                    "margin": "none",
                    "flex": 9,
                    "offsetStart": "md"
                }
                ],
                "margin": "none"
            },
            {
                "type": "image",
                "url": "{{Wx_url}}",
                "align": "end",
                "position": "absolute",
                "offsetStart": "190px",
                "offsetTop": "5px"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "image",
                        "url": "{{cloth_icon}}",
                        "size": "xxs",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": "{{cloth_text}}",
                        "size": "xxs",
                        "align": "center",
                        "margin": "sm",
                        "weight": "bold"
                    }
                    ],
                    "flex": 1
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "image",
                        "url": "{{cloth_icon}}",
                        "size": "xxs",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": "{{cloth_text}}",
                        "size": "xxs",
                        "align": "center",
                        "margin": "sm",
                        "weight": "bold"
                    }
                    ],
                    "flex": 1
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "width": "3px",
                    "backgroundColor": "#B7B7B7"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "image",
                        "url": "{{suggestion_icon}}",
                        "size": "xxs",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": "{{suggestion_text}}",
                        "size": "xxs",
                        "align": "center",
                        "margin": "sm",
                        "weight": "bold"
                    }
                    ],
                    "flex": 1
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "image",
                        "url": "{{suggestion_icon}}",
                        "size": "xxs",
                        "flex": 1
                    },
                    {
                        "type": "text",
                        "text": "{{suggestion_text}}",
                        "size": "xxs",
                        "align": "center",
                        "margin": "sm",
                        "weight": "bold"
                    }
                    ],
                    "flex": 1
                }
                ],
                "margin": "xxl"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "{{time_desc}}",
                        "margin": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "{{Wx_url}}",
                            "flex": 1,
                            "size": "xxs",
                            "offsetTop": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "{{minT}}° ~ {{maxT}}°",
                                    "weight": "bold"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                    {
                                        "type": "text",
                                        "text": "{{PoP}}%",
                                        "weight": "bold",
                                        "align": "center"
                                    }
                                    ],
                                    "backgroundColor": "#E0E0E0",
                                    "width": "40px",
                                    "height": "22px",
                                    "cornerRadius": "sm"
                                }
                                ],
                                "flex": 3,
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "{{cloth}}",
                                "weight": "bold"
                            }
                            ],
                            "flex": 3,
                            "margin": "md"
                        }
                        ],
                        "margin": "md"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "width": "3px",
                    "backgroundColor": "#B7B7B7",
                    "margin": "md",
                    "offsetTop": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "{{time_desc}}",
                        "margin": "md",
                        "weight": "bold"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                        {
                            "type": "image",
                            "url": "{{Wx_url}}",
                            "flex": 1,
                            "size": "xxs",
                            "offsetTop": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "{{minT}}° ~ {{maxT}}°",
                                    "weight": "bold"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                    {
                                        "type": "text",
                                        "text": "{{PoP}}%",
                                        "weight": "bold",
                                        "align": "center"
                                    }
                                    ],
                                    "backgroundColor": "#E0E0E0",
                                    "width": "40px",
                                    "height": "22px",
                                    "cornerRadius": "sm"
                                }
                                ],
                                "flex": 3,
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "{{cloth}}",
                                "weight": "bold"
                            }
                            ],
                            "flex": 3,
                            "margin": "md"
                        }
                        ],
                        "margin": "md"
                    }
                    ],
                    "flex": 1,
                    "margin": "md"
                }
                ]
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "width": "{{sun_width}}%",
                    "height": "6px",
                    "backgroundColor": "#64cbf3",
                    "offsetTop": "6px"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "icon",
                        "url": "https://cdn-icons-png.freepik.com/512/169/169367.png"
                    }
                    ],
                    "width": "16px",
                    "justifyContent": "center"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "height": "6px",
                    "backgroundColor": "#64cbf3",
                    "offsetTop": "6px"
                }
                ],
                "margin": "md"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "text",
                    "text": "日出 {{sunrise_time}}",
                    "weight": "bold",
                    "align": "start"
                },
                {
                    "type": "text",
                    "text": "日落 {{sunset_time}}",
                    "align": "end",
                    "weight": "bold"
                }
                ],
                "margin": "xs"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "width": "{{moon_width}}%",
                    "height": "6px",
                    "backgroundColor": "#1b2328",
                    "offsetTop": "6px"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                    {
                        "type": "icon",
                        "url": "https://cdn-icons-png.freepik.com/512/12470/12470176.png"
                    }
                    ],
                    "width": "16px",
                    "justifyContent": "center"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "height": "6px",
                    "backgroundColor": "#1b2328",
                    "offsetTop": "6px"
                }
                ],
                "margin": "none"
            },
            {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                {
                    "type": "text",
                    "text": "月出 {{moonrise_time}}",
                    "weight": "bold",
                    "align": "start"
                },
                {
                    "type": "text",
                    "text": "月落 {{moonset_time}}",
                    "align": "end",
                    "weight": "bold"
                }
                ],
                "margin": "xs"
            }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
            {
                "type": "button",
                "action": {
                "type": "message",
                "label": "回主選單",
                "text": "主選單"
                },
                "style": "primary",
                "margin": "md"
            }
            ]
        }
    }"""

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

    for i in range(2):
        params = {
            "cloth_text": cloth_text[i],
            "cloth_icon": cloth_icon[i],
            "suggestion_text": suggestion_text[i],
            "suggestion_icon": suggestion_icon[i]
        }
        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)

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

        line_flex_str = LineBotHelper.replace_variable(line_flex_str, params, 1)

    return line_flex_str

if __name__ == "__main__":
        app.run()