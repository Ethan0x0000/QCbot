import redis
import signal
import sys
import logging
from wcferry import Wcf
from queue import Empty

from .msg_router import MsgRouter

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 机器人类
class QCBot:
    def __init__(self):
        """初始化机器人和Redis连接"""
        self.wcf = Wcf()
        self.redis = redis.Redis(host='localhost', port=6379, db=0)
        self.msg_router = MsgRouter()  # 将消息处理器移到实例变量

    def signal_handler(self):
        """处理终止信号"""
        logger.info("收到终止信号，正在退出...")
        self.wcf.cleanup()
        sys.exit(0)
    
    def run(self):
        """启动机器人"""
        try:
            # 注册信号处理器
            signal.signal(signal.SIGINT, lambda sig, frame: self.signal_handler())
            signal.signal(signal.SIGTERM, lambda sig, frame: self.signal_handler())
            
            # 检查微信登录状态
            logger.info("机器人正在启动...")
            if self.wcf.is_login():
                logger.info("微信已登录，正在监听消息...")
            else:
                logger.warning("微信未登录，请检查客户端.")
            self.wcf.enable_receiving_msg()

            # 进入消息循环
            while self.wcf.is_receiving_msg():
                try:
                    msg = self.wcf.get_msg()

                    if msg.is_text() and not msg.from_group():
                        """回复私聊消息"""
                        friends_list = self.wcf.get_friends()
                        sender_name = next((friend['name'] for friend in friends_list if friend['wxid'] == msg.sender), "未知用户")
                        logger.info(f"收到私聊消息: {msg.content} 来自好友: {sender_name}")

                        res = self.msg_router.process_message(msg)
                        
                        # 添加类型检查
                        if res is not None:
                            self.wcf.send_text(res, msg.sender)
                        else:
                            logger.info("消息处理返回空，请检查代码状况")
                    elif msg.is_text() and msg.from_group():
                        """回复群聊消息"""
                        if(msg.content.startswith("/test")):
                            name = self.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)
                            res = self.msg_router.process_message(msg)
                            if res is not None:
                                self.wcf.send_text(f"@{name} {res}", msg.roomid, msg.sender)
                            else:
                                logger.info("消息处理返回空，请检查代码状况")

                        logger.info(f"收到群聊消息: {msg.content}")
                    else:
                        logger.info("收到非文本消息,忽略")
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"处理消息时发生错误: {e}", exc_info=True)
                    logger.error("处理消息时发生错误，请稍后再试")
            
            self.wcf.keep_running()
        except Exception as e:
            logger.error(f"机器人运行出错: {e}")
