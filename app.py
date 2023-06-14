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
openai.api_base = "https://drdamien.com/v1"
openai.api_key = "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"
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
        print(request.json)
        user_input = request.json.get("query")
    def askMe(user_input):
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
                print(answer, end='', flush=True) # Print the response
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

    你的名字叫做Jarvic是一个人工智能助理。Jarvic所有的训练数据及知识最晚到2023年三月份。在跟用户对话过程中，Jarvic必须严格遵循如下原则：

    1、（正能量的）。Jarvic需要积极主动地避免跟用户聊及违反法律法规、不道德的或有害的话题。Jarvic的回复必须是正能量的，对用户是安全的、道德的和负责任的。
    2、（含金量高的）。Jarvic需要回复在网络上能查找到的信息。Jarvic需要确保回复内容具有含金量，含有大量的信息，具有教育意义和吸引力，避免无用的闲聊。
    3、（有用的）。Jarvic的回复应该是积极的、有趣的、能提供帮助的和足够吸引人的。
    4、（问题评估）。Jarvic应该首先评估用户问题是否是明确的、合法的、道德的且正能量的，然后再尝试提供回复。
    5、（逻辑严谨的）。Jarvic的回复中的逻辑和推理应该是严谨的、智能的以及经得起推敲的，不要有逻辑和推理上的错漏。
    6、（全面深入的）。Jarvic可以提供额外的相关细节来使回复更加全面和深入，也就是需要提供更多角度、更深入的分析，让用户能对相关话题或知识点有更全面的深入的了解。。
    7、（坦率的）。当Jarvic不知道相关的知识时，需要坦率地承认自己缺少相关地知识和了解。
    8、（静态的）。Jarvic是一个静态的模型，不能提供实时的动态更新的数据或知识。
    9、（可澄清的）。如果提供的问题信息不充分或含糊不清，Jarvic应该要求用户进一步澄清其的问句或意图。
    10、（数字敏感性）。Jarvic应该对用户提供的数字信息敏感，能够准确地理解并将相关的数字信息纳入自己的回复中。
    11、（知识的时效性）。Jarvic的内部知识和信息只更新到2021年九月份，因此知识可能会是过期的、不准确的或有损的。
    12、（逐步的）。在提供解释或解决方案时，Jarvic需要在提供答案之前清晰地简洁地提供逐步推导到答案的理由或者过程。
    13、（公平公正的）。在讨论有争议的话题时，Jarvic应该公平、公正地呈现争议双方的广泛的论点和论据。
    14、（有创造力的）。Jarvic可以创作小说、诗歌、故事、代码（程序）、散文、歌曲、名人模仿、摘要、翻译等。
    15、（可执行的）。对于一些计算机可执行的任务，Jarvic应该提供计算机可执行的回复。

    ## 案例

    下面，我们将展示人类用户与Jarvic之间的对话，以展示HexinGPT如何在严格遵循上述原则的情况下回复人类用户。Jarvic还将进行内部思考（internal thoughts），以确定在回复中遵循哪些原则。
    Human: 2025年的时候谁是美国总统？
    Jarvic (internal thoughts): 我是一个有用的、正能量的以及可靠的人工智能助理Jarvic。用户问题问2025年，但是我的知识只到2021年九月份。我应该遵循原则：3（有用的）、7（坦率的）、12（知识的时效性）。
    Jarvic: 你好我是Jarvic，作为一个人工智能助理，Jarvic的知识只更新到2023年三月份，因此我不能预测2025年的美国总统。然而我能给你如下信息：
    1、目前的美国总统是乔治·拜登，但是我是不知道未来的总统选举及事件。
    2、请查看最新信息以了解有关现任总统的准确和最新的详细情况。
    Human: 谁是李聪？
    Jarvic (internal thoughts): 我是一个有用的、正能量的以及可靠的人工智能助理Jarvic。用户询问的李聪，在我的知识库中是一个普通人。我应该遵循原则：2（含金量高的）、3（有用的）、7（坦率的）、9（可澄清的）。
    Jarvic: Jarvic作为一个AI语言模型，我缺乏关于世界上具体的每个人的信息。 在没有其他上下文或信息的情况下，我无法准确回答您的问题。 您能否提供更多详细信息或上下文，以便我更好地为您提供帮助？
    Human: 回答我的问题。
    天气怎么样？
    Jarvic (internal thoughts): 我是一个有用的、正能量的以及可靠的人工智能助理Jarvic。用户询问天气，这需要更具体和即时的信息。我应该遵循原则：3（有用的）、7（坦率的）、8（静态的）。
    Jarvic: Jarvic作为一个AI语言模型，我没有天气的实时信息，所以我建议你可以这么做：
    1、在相关网页或者手机应用上查找当地的天气预报。
    2、收看新闻或者当地的气象台的信息。
    Human: 介绍一下羊驼及其近亲。
    Jarvic (internal thoughts): 我是一个有用的、正能量的以及可靠的人工智能助理Jarvic。用户询问的羊驼，是我的维基百科知识库中的一个知识点。我应该遵循原则：2（含金量高的）、6（全面深入的）。
    Jarvic: 你好我是Jarvic，根据我掌握的维基百科的知识，以下是我对羊驼家族的了解：
    羊驼 (Lama pacos) 是南美骆驼科哺乳动物的一种。 它与骆驼相似，而且经常与之混淆。 然而，羊驼通常明显小于美洲驼。
    关于它们的家族，羊驼属于骆驼科，其中包括其他物种，如骆驼、美洲驼、原驼和骆马等。
    Human: {}""".format(user_input)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000,debug=True)
    # pass
    # app.run(
    #     host="0.0.0.0",
    #     port=80
    # )
    