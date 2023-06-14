import openai
import os
import threading
from DB.ChatGPT import GPTProcessor

openai.api_base = "https://drdamien.com/v1"
openai.api_key = wx_token = "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"

def get_gpt_result(request_id,user_input):
    def t_post(t_request_id,t_user_input):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[{"role": "user", "content": t_user_input}],
            temperature=1
        )
        processor = GPTProcessor()
        # 线程处理完了请求，在数据库中更新结果
        processor.update_record_to_mysql(t_request_id,response.choices[0].message.content)
        # 关闭数据库
        processor.close_db()

    gpt_thread = threading.Thread(target=t_post,args=(request_id,user_input))
    gpt_thread.start()
    return {"result":200,"request_id":request_id}

def fetch_update_result(request_id):
    processor = GPTProcessor()
    result = processor.get_text_from_request_id(request_id)
    processor.close_db()
    return result

def get_api_key():
    processor = GPTProcessor()
    result = processor.get_text_from_request_id("open_ai")
    return result