import re  # 导入正则表达式模块
from wcferry import Wcf, WxMsg
from typing import Optional
from services import APIRouter, SignSystem, PicMaker
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MsgHandler:
    def __init__(self):
        self._ck = APIRouter()
        self._ss = SignSystem()
        self.params = { 'tag': None , 'name':None }

    def process_room_message(self, wcf: Wcf, msg: WxMsg) -> Optional[str]:
        """处理接收到的微信群聊消息"""
        content = msg.content.strip()

        if content == "签到":
            res = self._ss.sign(msg.sender)
            if res["success"]:
                ans = f"✅ 签到成功！\n获得积分：10+{res['continuous_days']-1}\n当前积分：{res['points']}\n连续签到：{res['continuous_days']}\n当前排名：{res['rank']}"
            elif res["already_signed"]:
                ans = f"⏰ 今日已签到\n当前积分：{res['points']}\n连续签到：{res['continuous_days']}\n当前排名：{res['rank']}"
            else:
                ans = "❌ 签到失败，请稍后重试"
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)}\n{ans}",msg.roomid, msg.sender)
            logger.info(f"触发签到事件")
        elif content.startswith("村庄"):
            #从content中提取出村庄标签，以#开头，为数字或字母
            match = re.search(r'(#[a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
            if match:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在请求数据并生成图片，大概需要5-30秒，请耐心等待...",msg.roomid, msg.sender)
                self.params['tag'] = match.group(1)  # 提取匹配的村庄标签
                res = self._ck.get_data('player_stats', self.params)
                if res:
                    pm = PicMaker("player_stats", res)
                    img_path = pm.generate()
                    wcf.send_image(img_path, msg.roomid)
                else:
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败，请稍后再试",msg.roomid, msg.sender)  
            else:      
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供村庄标签",msg.roomid, msg.sender)
            logger.info(f"触发查询村庄事件")
        elif content.startswith("玩家"):
            pass

    
    def process_person_message(self, wcf: Wcf, msg: WxMsg) -> Optional[str]:
        """处理接收到的微信私聊消息"""
        pass
        

    def sign_mode(self, query: str) -> Optional[str]:
        """查询游戏数据"""
        return "触发模式：游戏数据查询"

    def player_stats_mode(self, question: str) -> Optional[str]:
        """回答游戏相关问题"""
        return "触发模式：知识库问答"

    def player(self, content: str) -> Optional[str]:
        """娱乐互动回复"""
        return "触发模式：娱乐互动"
