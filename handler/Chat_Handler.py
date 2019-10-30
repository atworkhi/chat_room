# _*_coding:utf-8_*_
# ==========================================
#   FileName:Hello.py
#   User: hanxx
#   Date: 2019/9/12
#   Desc:  主处理函数
# ===========================================
import redis
import json
import hashlib


class ChatHandler(object):
    def __init__(self):
        # 初始化参数
        self.chat_room_nick_set = 'chat_room_nick_set'
        self.cookie_nick = 'cookie-{}'
        self.chat_list = 'chat_list'
        # 初始化数据连接
        self.client = redis.Redis(host='192.168.10.100', port='6379')

    def is_nick_already_exists(self, nick):
        # 判断你是否登录本昵称，如果登录了将不能使用
        # 添加到redis集合，如果添加返回1 则昵称之前不存在
        is_flag = self.client.sadd(self.chat_room_nick_set, nick)
        if is_flag == 1:
            return False
        return True

    def set_token(self, nick, token):
        # 设定Token，只需要登录一次，以后直接访问就行
        # 使用redis字符串实现：cookie-昵称
        key = self.cookie_nick.format(nick)
        self.client.set(key, token)

    def get_token(self, nick):
        # 获取Token 如果不存在返回None
        key = self.cookie_nick.format(nick)
        token = self.client.get(key)
        return None if not token else token.decode()

    def get_chat_list(self):
        # 获取聊天列表 获取前20条消息
        chat_list = self.client.lrange(self.chat_list, -20, -1)
        chat_info_list = []
        for chat in chat_list:
            print(chat)
            chat_info = json.loads(chat)
            chat_info_list.append(chat_info)
        return chat_info_list

    def get_nick_msg_expire_time(self, nick, msg):
        """
        为了防止信息太长，因此把信息编码为md5以后再与昵称拼接以缩短Key的长度。
        使用Redis的ttl命令来实现，ttl命令如果返回None，说明不存在这个Key，
        返回None。如果ttl返回-1，说明这个Key没有设定过期时间，这个Key可以一直存在
        如果ttl返回一个大于0的正整数，说明在这个整数对应的秒过于以后，Redis会自动
        删除这个Key
        """
        msg_md5 = hashlib.md5(msg.encode()).hexdigest()
        duplicate_msg_check_flag = nick + msg_md5
        expire_time = self.client.ttl(duplicate_msg_check_flag)
        return expire_time

    def push_chat_info(self, chat_info):
        # 将聊天信息列入列表右侧
        self.client.rpush(self.chat_list, json.dumps(chat_info))
        self.client.ltrim(self.chat_list, -20, -1)

    def set_nick_msg_expire_time(self, nick, msg):
        # 设定key过期时间，限定一个用户2分钟不能发送重复内容
        msg_md5 = hashlib.md5(msg.encode()).hexdigest()
        duplicate_msg_check_flag = nick + msg_md5
        self.client.set(duplicate_msg_check_flag, 1, ex=120)
