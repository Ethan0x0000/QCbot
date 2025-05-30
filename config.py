import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 服务配置
SEND_MESSAGE_URL = os.getenv("SEND_MESSAGE_URL", "http://127.0.0.1:2022/KP")  # 发送消息的目标地址
RECEIVE_MESSAGE_PORT = int(os.getenv("RECEIVE_MESSAGE_PORT", "8080"))  # 接收消息的端口
HOST = os.getenv("HOST", "127.0.0.1")  # 服务主机地址 