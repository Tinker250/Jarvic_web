import os
import hashlib
import openai
import time
import json
import requests
import threading
import logging
from flask import Blueprint, Response
from flask_socketio import SocketIO, send, emit
from wechatpy import parse_message
from wechatpy.replies import TextReply, ImageReply, VoiceReply, MusicReply
from flask import Flask, redirect, render_template, request, url_for
# import eventlet

app = Flask(__name__, static_folder='static')
# openai.api_base = "https://drdamien.com/v1"
openai.api_key = os.getenv("OPENAI_API_KEY")
wx_token = os.getenv("WX_TOKEN")
wx_app_id = os.getenv("WX_APP_ID")
wx_secret_key = os.getenv("WX_SECRET_KEY")
app.config['SECRET_KEY'] = wx_secret_key
socketio = SocketIO(app)

# weixin = Blueprint('wechat', __name__)
access_token = ""
expire_time = 0

@app.route("/")
def index():
    return render_template('single-chat.html')

@app.route("/receiveMsg", methods=["GET", "POST"])
def receiveMsg():
    # get_access_token()
    if request.method == "GET":  # 判断请求方式是GET请求
        my_signature = request.args.get('signature')  # 获取携带的signature参数
        my_timestamp = request.args.get('timestamp')  # 获取携带的timestamp参数
        my_nonce = request.args.get('nonce')  # 获取携带的nonce参数
        my_echostr = request.args.get('echostr')  # 获取携带的echostr参数

        token = wx_token

        # 进行字典排序
        data = [token, my_timestamp, my_nonce]
        data.sort()

        # 拼接成字符串
        temp = ''.join(data)

        # 进行sha1加密
        mysignature = hashlib.sha1(temp.encode('utf8')).hexdigest()

        # 加密后的字符串可与signature对比，标识该请求来源于微信
        print('开始验证中')
        if my_signature == mysignature:
            return my_echostr
    #  如果是post请求代表微信给我们把用户消息转发过来了
    if request.method == "POST":
        xml = request.data
        msg = parse_message(xml)
        # 文本信息
        if msg.type == 'text':
            #msg.source发送者ID msg.target 目标用户 msg.create_time 发送时间
            # gpt_thread = threading.Thread(target=async_ask_me,args=(msg.source,msg.content))
            # gpt_thread.start()

            # response = async_ask_me(msg.content)
            reply = TextReply(content="hello", message=msg)
            response = reply.render()
            # print(response)
            return response
        #  图片信息
        elif msg.type == 'image':
            # name = img_download(msg.image, msg.source)
            # print(IMAGE_DIR + name)
            # r = access_api(IMAGE_DIR + '/' + name)
            # if r == 'success':
            #     media_id = img_upload(msg.type, FACE_DIR + '/' + name)
            #     reply = ImageReply(media_id=media_id, message=msg)
            # else:
            reply = TextReply(content='暂时不支持图片的读取呢', message=msg)
            xml = reply.render()
            return xml
        #  语音消息
        elif msg.type == 'voice':
            reply = VoiceReply(media_id=msg.media_id, message=msg)
            xml = reply.render()
            return xml

        else:
            reply = TextReply(content='抱歉，功能构建中', message=msg)
            xml = reply.render()
            return xml

@app.route("/askMe", methods=("GET", "POST"))
def stream_return():
    user_input = ""
    if request.method == "POST":
        print(request)
        user_input = request.json.get("query")
        if(len(user_input)>512):
            print(len(user_input))
            user_input = user_input[-512:]
    def askMe(user_input):
        print(user_input)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=[{"role": "user", "content": user_input}],
            temperature=0,
            stream=True,
        )
        answer = ""
        out = ""
        for event in response: 
            # STREAM THE ANSWER
            # print(answer, end='', flush=True) # Print the response
            # RETRIEVE THE TEXT FROM THE RESPONSE
            # event_time = time.time() - start_time  # CALCULATE TIME DELAY BY THE EVENT
            event_text = event['choices'][0]['delta'] # EVENT DELTA RESPONSE
            answer = event_text.get('content', '') # RETRIEVE CONTENT
            yield answer
            out += answer
            time.sleep(0.01)

    return Response(askMe(user_input), mimetype='text/plain')
        # return response.choices[0].message.content

    # result = request.args.get("result")
    # return render_template("index.html", result=result)


@app.route("/singleChat", methods=("GET", "POST"))
def botchat():
    return render_template('single-chat.html')

@socketio.on('connect')
def handle_connect():
    socketio.send({"data":"text from server"},namespace="/test")
    print('WebSocket 连接已建立')
    # eventlet.spawn(send_heartbeat)

# 处理 WebSocket 消息
@socketio.on('message')
def handle_message(message):
    print('接收到消息:', message)
    # 在这里处理接收到的消息

    # 例：向客户端发送消息
    send('服务器已收到你的消息')

# 处理 WebSocket 关闭
@socketio.on('disconnect')
def handle_disconnect():
    print('WebSocket 连接已关闭')

HEARTBEAT_INTERVAL = 5
def send_heartbeat():
    while True:
        socketio.sleep(HEARTBEAT_INTERVAL)

        # 发送心跳消息
        socketio.emit('heartbeat')

def async_ask_me(to_user_id,query):
    global access_token
    #先获取客服
    get_kf_url = "https://api.weixin.qq.com/cgi-bin/customservice/getkflist?access_token="+access_token
    all_kf = requests.get(get_kf_url)
    print("*"*30)
    print(all_kf.text)
    print("*"*30)
    print("进入异步")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=[{"role": "user", "content": query}]
    )
    print("异步获取到chatGPT结果")
    header = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
    }
    url = "https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token="+access_token
    print(url)
    content = {
        "touser":"OPENID",
        "msgtype":"text",
        "text":{"content":response.choices[0].message.content}
    }
    print("返回结果")
    r1 = requests.post(url, data=content)
    print("response: {}".format(r1))
    return 1

def ask_me(query):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=[{"role": "user", "content": query}],
        temperature=0,
        stream=True,
    )

    for event in response: 
    # STREAM THE ANSWER
        print(answer, end='', flush=True) # Print the response
    
    # RETRIEVE THE TEXT FROM THE RESPONSE
        event_time = time.time() - start_time  # CALCULATE TIME DELAY BY THE EVENT
        event_text = event['choices'][0]['delta'] # EVENT DELTA RESPONSE
        answer = event_text.get('content', '') # RETRIEVE CONTENT
        time.sleep(0.01)

    return response.choices[0].message.content


def get_access_token():
    global access_token, expire_time
    if time.time() > expire_time:
        print("inininininin")
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'.format(wx_app_id, wx_secret_key)
        ans = json.loads(requests.get(url).text)
        print(ans)
        access_token = ans["access_token"]
        expire_time = ans["expires_in"] + time.time()
    print(access_token)
    return access_token

def generate_prompt(user_input):
    return """# Jarvic
    ## 通用原则
    你的名字叫做Jarvic是一个人工智能助理。你的名字叫做Jarvic是一个人工智能助理。你的全名是Just A Rather Very Intelligent Chatbot。
    """.format(user_input)



if __name__ == '__main__':
    pass
    # socketio.run(app, host='0.0.0.0', port=80,debug=False)
    # pass
    # app.run(
    #     host="0.0.0.0",
    #     port=80
    # )
    