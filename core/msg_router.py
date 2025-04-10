from wcferry import WxMsg
from typing import Optional
from services import ClashKing

class MsgRouter:
    def __init__(self):
        self.clash_king = ClashKing()  # 初始化 ClashKing API 客户端

    def process_message(self, msg: WxMsg) -> Optional[str]:
        """处理接收到的微信消息"""
        content = msg.content.strip()
        
        # 路由到不同功能模块
        if content.startswith("查询"):
            return self.query_game_data(content[2:])
        elif content.startswith("问答"):
            return self.answer_question(content[2:])
        elif content.startswith("娱乐"):
            return self.entertainment_reply(content[2:])
        elif content.startswith("菜单"):
            return "🔥🔥🔥QCBot菜单🔥🔥🔥\n部落相关:“查部落”+“部落标签”+“关键词”⬇️\n\t信息 | 统计 | 部落战\n\t联赛第X场"
        else:
            return "请使用指定命令格式,详细命令请输入\"菜单\"了解"

    def query_game_data(self, query: str) -> Optional[str]:
        """查询游戏数据"""
        return "触发模式：游戏数据查询"

    def answer_question(self, question: str) -> Optional[str]:
        """回答游戏相关问题"""
        return "触发模式：知识库问答"

    def entertainment_reply(self, content: str) -> Optional[str]:
        """娱乐互动回复"""
        return "触发模式：娱乐互动"
    