import requests
from datetime import datetime

class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key

    api_map = {"宜蘭縣":"F-D0047-003","桃園市":"F-D0047-007","新竹縣":"F-D0047-011","苗栗縣":"F-D0047-015",
                "彰化縣":"F-D0047-019","南投縣":"F-D0047-023","雲林縣":"F-D0047-027","嘉義縣":"F-D0047-031",
                "屏東縣":"F-D0047-035","臺東縣":"F-D0047-039","花蓮縣":"F-D0047-043","澎湖縣":"F-D0047-047",
                "基隆市":"F-D0047-051","新竹市":"F-D0047-055","嘉義市":"F-D0047-059","臺北市":"F-D0047-063",
                "高雄市":"F-D0047-067","新北市":"F-D0047-071","臺中市":"F-D0047-075","臺南市":"F-D0047-079",
                "連江縣":"F-D0047-083","金門縣":"F-D0047-087"}

    # 取得12小時天氣預報
    def get_12hr_forecast(self, city, town):
        city_id = __class__.api_map[city]
        weather_elements = {
            "天氣現象": "Wx",
            "12小時降雨機率": {"name": "PoP12h", "element": "ProbabilityOfPrecipitation"},
            "最低溫度": {"name": "MinT", "element": "MinTemperature"},
            "最高溫度": {"name": "MaxT", "element": "MaxTemperature"},
            "最低體感溫度": {"name": "MinAT", "element": "MinApparentTemperature"},
            "最高體感溫度": {"name": "MaxAT", "element": "MaxApparentTemperature"},
            "平均相對濕度": {"name": "RH", "element": "RelativeHumidity"},
            "紫外線指數": {"name":"UVI", "element": "UVIndex"},
            "風速": {"name": "WS", "element": "BeaufortScale"}
        }
        result = {}
        for i, element in enumerate(weather_elements.keys()):
            api_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-093?locationId={city_id}&LocationName={town}&ElementName={element}&format=JSON"
            response = self.get_weather(api_url)
            if response:
                data = response.json()
                weather_data = data["records"]["Locations"][0]["Location"][0]["WeatherElement"][0]["Time"]
                # 第一次取得資料時，取得start_time和end_time
                if i == 0:
                    result["start_time"] = [self.convert_time_format(weather["StartTime"]) for weather in weather_data]
                    result["end_time"] = [self.convert_time_format(weather["StartTime"]) for weather in weather_data]
                if element == "天氣現象":
                    result["Wx_desc"] = [weather["ElementValue"][0]["Weather"] for weather in weather_data]
                    result["Wx_code"] = [weather["ElementValue"][0]["WeatherCode"] for weather in weather_data]
                else:
                    result[weather_elements[element]["name"]] = [
                        weather["ElementValue"][0][weather_elements[element]["element"]]
                        for weather in weather_data
                    ]
            else:
                print(f"Failed to get weather data for {city}{town}. Status code: {response.status_code}")
        return result
    
    # 取得天文時刻
    def get_astronomical_time(self, city):
        # 日出日落/月出月落
        astronomical_api = ["https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0062-001", "https://opendata.cwa.gov.tw/api/v1/rest/datastore/A-B0063-001"]
        astronomical_data = {}
        now = datetime.now().strftime('%Y-%m-%d')
        for api in astronomical_api:
            api = f"{api}?CountyName={city}&Date={now}"
            response = self.get_weather(api)
            if response:
                data = response.json()
                result = data["records"]["locations"]["location"][0]["time"][0]
                astronomical_data.update(result)
            else:
                print(f"Failed to get astronomical data. Status code: {response.status_code}")
        return astronomical_data
    
    # call API取得氣象資料
    def get_weather(self, api_url):
        headers = {"Authorization": self.api_key}
        response = requests.get(api_url, headers=headers)
        return response if response.status_code == 200 else None
    
    # 轉換時間格式 MM/DD HH:MM
    def convert_time_format(self, time_str):
        datetime_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S+08:00")
        return datetime_obj
    
    # 轉換星期
    def convert_to_weekday(self, datetime):
        week = datetime.weekday() + 1
        if week == 1:
            return "一"
        elif week == 2:
            return "二"
        elif week == 3:
            return "三"
        elif week == 4:
            return "四"
        elif week == 5:
            return "五"
        elif week == 6:
            return "六"
        elif week == 7:
            return "日"
    
    # 取得時間描述
    def get_time_desc(self, datetime):
        match datetime.hour:
            case 6 | 9 | 12 | 15: 
                return ["今日白天", "今晚明晨", "明日白天"]
            case 0 | 3 |18 | 21:
                return ["今晚明晨", "明日白天", "明日晚上"]
            case _:
                return ["-", "-", "-"]
    
    # 取得穿搭建議
    def get_suggestions(self, url_root, weather_data, index):
        cloth_map = {
            "短袖": f"{url_root}static/suggestion_icons/short_sleeves.png",
            "薄長袖": f"{url_root}static/suggestion_icons/thin_long_sleeves.png",
            "厚長袖": f"{url_root}static/suggestion_icons/thick_long_sleeves.png",
            "薄外套": f"{url_root}static/suggestion_icons/thin_jacket.png",
            "棉外套": f"{url_root}static/suggestion_icons/cotton_jacket.png",
            "羽絨外套": f"{url_root}static/suggestion_icons/down_jacket.png"
        }
        suggestion_map = {
            "注意高溫": f"{url_root}static/suggestion_icons/heat.png",
            "注意低溫": f"{url_root}static/suggestion_icons/cold.png",
            "攜帶雨具": f"{url_root}static/suggestion_icons/rain.png",
            "注意防曬": f"{url_root}static/suggestion_icons/uvi.png",
            "注意強風": f"{url_root}static/suggestion_icons/wind.png",
            "適合運動": f"{url_root}static/suggestion_icons/exercise_s.png",
            "減少運動": f"{url_root}static/suggestion_icons/exercise_r.png",
            "避免運動": f"{url_root}static/suggestion_icons/exercise_a.png",
            "適合曬衣": f"{url_root}static/suggestion_icons/hang_s.png",
            "減少曬衣": f"{url_root}static/suggestion_icons/hang_r.png",
            "避免曬衣": f"{url_root}static/suggestion_icons/hang_a.png"
        }
        minAT = int(weather_data["MinAT"][index])
        maxAT = int(weather_data["MaxAT"][index])
        PoP = int(weather_data["PoP12h"][index])
        WS = int(weather_data["WS"][index].split(" ")[1]) if " " in weather_data["WS"][index] else int(weather_data["WS"][index])
        UVI = int(weather_data["UVI"][index])
        RH = int(weather_data["RH"][index])
        clothes = []
        suggestions = []

        # 衣物建議條件
        if maxAT >= 23:
            clothes.append("短袖")
        elif maxAT >= 18:
            clothes.append("薄長袖")
        else:
            clothes.append("厚長袖")

        if minAT <= 12:
            clothes.append("羽絨外套")
        elif minAT <= 17:
            clothes.append("棉外套")
        elif minAT <= 23:
            clothes.append("薄外套")

        # 天氣建議條件
        if maxAT >= 36:
            suggestions.append("注意高溫")
        if minAT <= 12:
            suggestions.append("注意低溫")
        if PoP >= 30:
            suggestions.append("攜帶雨具")
        if UVI >= 8:
            suggestions.append("注意防曬")
        if WS >= 6:
            suggestions.append("注意強風")
        
        # 運動建議條件
        if PoP >= 50 or maxAT >= 38 or minAT <= 10:
            suggestions.append("避免運動")
        elif PoP >= 30 or maxAT >= 36 or minAT <= 12 or UVI >= 10:
            suggestions.append("減少運動")
        else:
            suggestions.append("適合運動")
        
        # 曬衣建議條件
        if RH >= 90:
            suggestions.append("避免曬衣")
        elif RH >= 80:
            suggestions.append("減少曬衣")
        else:
            suggestions.append("適合曬衣")

        return clothes, [cloth_map[cloth] for cloth in clothes], suggestions, [suggestion_map[suggestion] for suggestion in suggestions]