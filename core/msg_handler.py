import re  # 导入正则表达式模块
from wcferry import Wcf, WxMsg
from typing import Optional
from services import ClashKing
from services import SignSystem
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MsgHandler:
    def __init__(self):
        self._ck = ClashKing()
        self._sss = SignSystem()

    def process_room_message(self, wcf: Wcf, msg: WxMsg) -> Optional[str]:
        """处理接收到的微信群聊消息"""
        content = msg.content.strip()

        if content == "签到":
            res = self._sss.sign(msg.sender)
            if res["success"]:
                ans = f"✅ 签到成功！\n获得积分：10+{res['continuous_days']-1}\n当前积分：{res['points']}\n连续签到：{res['continuous_days']}\n当前排名：{res['rank']}"
            elif res["already_signed"]:
                ans = f"⏰ 今日已签到\n当前积分：{res['points']}\n连续签到：{res['continuous_days']}\n当前排名：{res['rank']}"
            else:
                ans = "❌ 签到失败，请稍后重试"
            logger.info(f"触发签到事件")
        elif content.startwith("村庄"):
            #从content中提取出村庄标签，以#开头，为数字或字母
            match = re.search(r'#([a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
            if match:
                village_tag = match.group(1)  # 提取匹配的村庄标签
                
            else:
                ans = "❌ 未找到有效的村庄标签"

            logger.info(f"触发查询村庄事件，但未找到有效的村庄标签")
        
        wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)}\n{ans}",msg.roomid, msg.sender)
        # # 路由到不同功能模块
        # if content.startswith("查询"):
        #     return self.query_game_data(content[2:])
        # elif content.startswith("问答"):
        #     return self.answer_question(content[2:])
        # elif content.startswith("娱乐"):
        #     return self.entertainment_reply(content[2:])
        # elif content.startswith("菜单"):
        #     return "🔥🔥🔥QCBot菜单🔥🔥🔥\n部落相关:“查部落”+“部落标签”+“关键词”⬇️\n\t信息 | 统计 | 部落战\n\t联赛第X场"
        # else:
        #     return "请使用指定命令格式,详细命令请输入\"菜单\"了解"

    
    def process_person_message(self, wcf: Wcf, msg: WxMsg) -> Optional[str]:
        """处理接收到的微信私聊消息"""
        pass
        

    def query_game_data(self, query: str) -> Optional[str]:
        """查询游戏数据"""
        return "触发模式：游戏数据查询"

    def answer_question(self, question: str) -> Optional[str]:
        """回答游戏相关问题"""
        return "触发模式：知识库问答"

    def entertainment_reply(self, content: str) -> Optional[str]:
        """娱乐互动回复"""
        return "触发模式：娱乐互动"
