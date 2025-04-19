import signal
import sys
import logging
from wcferry import Wcf
from queue import Empty
from .msg_handler import MsgHandler

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 机器人类
class QCBot:
    def __init__(self):
        """初始化机器人和消息处理"""
        self.wcf = Wcf()
        self.msg_handler = MsgHandler()

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
                logger.warning("微信未登录，请扫码登录...")
  
            self.wcf.enable_receiving_msg()

            # 进入消息循环
            while self.wcf.is_receiving_msg():
                try:
                    msg = self.wcf.get_msg()

                    if msg.is_text() and not msg.from_group():
                        """回复私聊消息"""
                        friends_list = self.wcf.get_friends()
                        sender_name = next((friend['name'] for friend in friends_list if friend['wxid'] == msg.sender), "未知用户")
                        logger.info(f"收到私聊消息: {msg.content} - 来自好友[{sender_name}]")

                        self.msg_handler.process_person_message(self.wcf, msg)

                    elif msg.is_text() and msg.from_group():
                        """回复群聊消息"""
                        contacts_list = self.wcf.get_contacts()
                        sender_room_name = next((contact['name'] for contact in contacts_list if contact['wxid'] == msg.roomid), "未知群组")
                        logger.info(f"收到群聊消息: {msg.content} - 来自群[{sender_room_name}]中成员:[{self.wcf.get_alias_in_chatroom(msg.sender, msg.roomid)}]")

                        if sender_room_name == "测试群":
                            self.msg_handler.process_room_message(self.wcf, msg)

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
