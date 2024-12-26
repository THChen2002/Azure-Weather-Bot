from config import Config
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    ShowLoadingAnimationRequest
)
import re

config = Config()
configuration = config.configuration

class LineBotHelper:        
    @staticmethod
    def reply_message(event, messages: list):
        """
        回覆多則訊息
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=messages
                )
            )
    
    @staticmethod
    def show_loading_animation(event):
        """
        顯示載入動畫
        """
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.show_loading_animation(ShowLoadingAnimationRequest(chatId=event.source.user_id))
        
    @staticmethod
    def replace_variable(text: str, variable_dict: dict, max_count: int = 0):
        """Returns 取代變數後的文字 e.g. {{semester}} -> 代表semester是一個變數，取代成variable_dict中key為semester的值(max_count為相同變數取代次數)
        str: 取代變數後的文字
        """
        replaced_count = {}

        def replace(match):
            key = match.group(1)
            if max_count:
                if key not in replaced_count:
                    replaced_count[key] = 1
                else:
                    replaced_count[key] += 1
                    if replaced_count[key] > max_count:
                        return match.group(0)
            return str(variable_dict.get(key, match.group(0)))

        # 匹配 {{variable}} 的正規表達式
        pattern = r'\{\{([a-zA-Z0-9_]*)\}\}'
        replaced_text = re.sub(pattern, replace, text)
        return replaced_text