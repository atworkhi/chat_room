# _*_coding:utf-8_*_
# ==========================================
#   FileName:Hello.py
#   User: hanxx
#   Date: 2019/9/12
#   Desc: flask主文件
# ===========================================
from flask import Flask, render_template, request, redirect
import json
import datetime
import hashlib
import time
from handler.Chat_Handler import ChatHandler
from urllib.parse import quote, unquote

app = Flask(__name__)
# 实例化
chatHandler = ChatHandler()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    request_data = request.json
    nick = request_data.get('nick', '')
    if not nick:
        return json.dumps({'success': False, 'reason': '昵称为空'}, ensure_ascii=False)
    if chatHandler.is_nick_already_exists(nick):
        return json.dumps({'success': False, 'reason': '昵称：{nick}已经被人占用！'.format(nick=nick)}, ensure_ascii=False)
    token = nick + str(time.time())
    token_md5 = hashlib.md5(token.encode()).hexdigest()
    chatHandler.set_token(nick, token_md5)
    response = app.make_response(json.dumps({'success': True, 'token': token_md5}))
    response.set_cookie('name', quote(nick, safe=''))
    response.set_cookie('token', token_md5)
    return response


@app.route('/room')
def room():
    nick = request.cookies.get('name', '')
    token = request.cookies.get('token', '')

    nick = unquote(nick)
    saved_token = chatHandler.get_token(nick)
    if token == saved_token:
        return render_template('chatroom.html')
    return redirect('/')


@app.route('/get_chat_list')
def get_chat_list():
    chat_list = chatHandler.get_chat_list()
    return json.dumps(chat_list, ensure_ascii=False)


@app.route('/post_message', methods=['POST'])
def post_message():
    message = request.json
    msg = message.get('msg', '')
    nick = message.get('nick', '')
    if not all([msg, nick]):
        return json.dumps({'success': False, 'reason': '昵称或聊天内容为空！'}, ensure_ascii=False)

    expire_time = chatHandler.get_nick_msg_expire_time(nick, msg)
    if expire_time < 1:
        message_info = {'msg': message['msg'],
                        'post_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'nick': message['nick']}
        chatHandler.push_chat_info(message_info)
        chatHandler.set_nick_msg_expire_time(nick, msg)
        return json.dumps({'success': True})
    elif expire_time >= 1:
        return json.dumps({'success': False,
                           'reason': '在两分钟内不同发送同样的内容！还剩{expire_time}秒'.format(expire_time=expire_time)},
                          ensure_ascii=False)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001)
