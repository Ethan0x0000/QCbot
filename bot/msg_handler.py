import re
from typing import Optional
import time
import requests
from services import APIRouter, SignSystem, PicMaker
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MsgHandler:
    def __init__(self):
        self._api = APIRouter()
        self._ss = SignSystem()
        self.params = { 'tag': "", 'name': "", 'season': ""}

    def process_room_message(self, message: dict) -> dict:
        """处理接收到的群聊消息"""
        content = message.get("content", "").strip()
        room_id = message.get("room_id")
        sender = message.get("sender")
        
        if content == "菜单" or content == "功能":
            return {
                "type": "text",
                "content": f"@{sender} 当前功能：\n1. 查村庄\n2. 查部落\n3. 查玩家\n4. 签到",
                "room_id": room_id
            }
        elif content == "签到":
            return self.sign_mode(message)
        elif content.startswith("查村庄") or content.startswith("查玩家"):
            return self.player_info_mode(message)
        elif content.startswith("查冲杯"):
            return self.player_legend_mode(message)
        elif content.startswith("搜玩家"):
            return self.player_search_mode(message)
        elif content.startswith("查实力"):
            return self.player_warhits_mode(message)
        elif content.startswith("查待办"):
            return self.player_todo_mode(message)
        elif content.startswith("查部落"):
            return self.clan_info_mode(message)
        elif content.startswith("查对战"):
            return self.clan_war_mode(message)
        elif content.startswith("查突袭"):
            return self.clan_raids_mode(message)
        else:
            return {"status": "ignored"}

    def process_person_message(self, message: dict) -> dict:
        """处理接收到的私聊消息"""
        return {"status": "not_implemented"}
        

    def sign_mode(self, message: dict) -> dict:
        """签到模式"""
        res = self._ss.sign(message.get("sender"))
        if res["success"]:
            ans = f"✅ 签到成功！\n获得积分：10+{res['continuous_days']-1}\n当前积分：{res['points']}\n连续签到：{res['continuous_days']}\n当前排名：{res['rank']}"
        elif res["already_signed"]:
            ans = f"⏰ 今日已签到\n当前积分：{res['points']}\n连续签到：{res['continuous_days']}\n当前排名：{res['rank']}"
        else:
            ans = "❌ 签到失败，请稍后重试"
            
        return {
            "type": "text",
            "content": f"@{message.get('sender')}\n{ans}",
            "room_id": message.get("room_id")
        }


    def player_info_mode(self, message: dict) -> dict:
        """查询村庄模式"""
        content = message.get("content", "").strip()
        room_id = message.get("room_id")
        sender = message.get("sender")
        
        match = re.search(r'(#[a-zA-Z0-9]+)', content)
        if not match:
            return {
                "type": "text",
                "content": f"@{sender} ❌ 请提供正确的村庄标签（#开头）。",
                "room_id": room_id
            }

        self.params['tag'] = match.group(1)
        timestamp = int(time.time())
        filename = f"player_info_{self.params['tag']}_{timestamp}.png"

        res = self._api.get_data('player_info', self.params)
        status_code = res.get('status_code')
        content_type = res.get('content_type')
        data = res.get('content')
        error_msg = res.get('error')

        if status_code == 200 and content_type == 'json' and data:
            try:
                pm = PicMaker("player_info", data)
                img_path = pm.generate(filename)
                if img_path:
                    return {
                        "type": "image",
                        "path": img_path,
                        "room_id": room_id
                    }
                else:
                    return {
                        "type": "text",
                        "content": f"@{sender} ✅ 查询成功，但图片生成失败。",
                        "room_id": room_id
                    }
            except Exception as e:
                logger.error(f"PicMaker failed for player_info: {e}")
                return {
                    "type": "text",
                    "content": f"@{sender} ❌ 图片生成过程中出错，请联系管理员。",
                    "room_id": room_id
                }
        elif status_code == 403:
            return {
                "type": "text",
                "content": f"@{sender} ❌ API认证失败，请联系管理员。",
                "room_id": room_id
            }
        elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
            return {
                "type": "text",
                "content": f"@{sender} 🚧 服务器正在维护中，请稍后再试...",
                "room_id": room_id
            }
        elif status_code == 555:
            return {
                "type": "text",
                "content": f"@{sender} ❌ 查询成功，但无法解析返回的数据格式。",
                "room_id": room_id
            }
        else:
            error_detail = f"状态码: {status_code}" if status_code else ""
            if error_msg:
                error_detail += f", 错误: {error_msg}"
            return {
                "type": "text",
                "content": f"@{sender} ❌ 请求失败。{error_detail}",
                "room_id": room_id
            }

    def player_legend_mode(self, message: dict) -> dict:
        """查询冲杯模式"""
        content = message.get("content", "").strip()
        room_id = message.get("room_id")
        sender = message.get("sender")
        
        match = re.search(r'(#[a-zA-Z0-9]+)', content)
        if not match:
            return {
                "type": "text",
                "content": f"@{sender} ❌ 请提供正确的村庄标签（#开头）。",
                "room_id": room_id
            }

        self.params['tag'] = match.group(1)
        timestamp = int(time.time())
        filename = f"player_legend_{self.params['tag']}_{timestamp}.png"

        # 获取当前赛季
        res = self._api.get_data("list_season", self.params)
        data = res.get('content')
        current_season = data[0] if data else ""
        self.params['season'] = current_season

        res = self._api.get_data('player_legend', self.params)
        status_code = res.get('status_code')
        content_type = res.get('content_type')
        data = res.get('content')
        error_msg = res.get('error')

        if status_code == 200 and content_type == 'json' and data:
            try:
                pm = PicMaker("player_legend", data)
                img_path = pm.generate(filename)
                if img_path:
                    return {
                        "type": "image",
                        "path": img_path,
                        "room_id": room_id
                    }
                else:
                    return {
                        "type": "text",
                        "content": f"@{sender} ✅ 查询成功，但图片生成失败。",
                        "room_id": room_id
                    }
            except Exception as e:
                logger.error(f"PicMaker failed for player_legend: {e}")
                return {
                    "type": "text",
                    "content": f"@{sender} ❌ 图片生成过程中出错，请联系管理员。",
                    "room_id": room_id
                }
        elif status_code == 403:
            return {
                "type": "text",
                "content": f"@{sender} ❌ API认证失败，请联系管理员。",
                "room_id": room_id
            }
        elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
            return {
                "type": "text",
                "content": f"@{sender} 🚧 服务器正在维护中，请稍后再试...",
                "room_id": room_id
            }
        elif status_code == 555:
            return {
                "type": "text",
                "content": f"@{sender} ❌ 查询成功，但无法解析返回的数据格式。",
                "room_id": room_id
            }
        else:
            error_detail = f"状态码: {status_code}" if status_code else ""
            if error_msg:
                error_detail += f", 错误: {error_msg}"
            return {
                "type": "text",
                "content": f"@{sender} ❌ 请求失败。{error_detail}",
                "room_id": room_id
            }

    def player_search_mode(self, wcf: Wcf, msg: WxMsg, content: str) -> Optional[str]:
        """查询玩家模式"""
        # 移除 "查玩家 " 前缀
        query_content = content[len("查玩家 "):].strip()
        if not query_content:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供玩家名称。", msg.roomid, msg.sender)
            return

        # 使用局部 params 字典
        params = {'name': "", 'league': "", 'townhall': "", 'exp': "", 'trophies': ""}

        # 第一个非关键词部分是玩家名称
        parts = query_content.split(maxsplit=1)
        player_name = parts[0]
        params['name'] = player_name

        # 如果只有玩家名称，remaining_content 为空字符串
        remaining_content = parts[1] if len(parts) > 1 else ""

        league_map = {
            "未排名": "Unranked",
            # 传奇联赛
            "传奇": "Legend League",
            # 泰坦联赛
            "泰坦一": "Titan League I",
            "泰坦二": "Titan League II",
            "泰坦三": "Titan League III",
            # 冠军联赛
            "冠军一": "Champion League I",
            "冠军二": "Champion League II",
            "冠军三": "Champion League III",
            
            # 大师联赛
            "大师一": "Master League I",
            "大师二": "Master League II",
            "大师三": "Master League III",
            
            # 水晶联赛
            "水晶一": "Crystal League I",
            "水晶二": "Crystal League II",
            "水晶三": "Crystal League III",
            
            # 黄金联赛
            "黄金一": "Gold League I",
            "黄金二": "Gold League II",
            "黄金三": "Gold League III",
            
            # 白银联赛
            "白银一": "Silver League I",
            "白银二": "Silver League II",
            "白银三": "Silver League III",
            
            # 青铜联赛
            "青铜一": "Bronze League I",
            "青铜二": "Bronze League II",
            "青铜三": "Bronze League III"
        }

        # 定义关键词和参数名的映射以及验证函数
        keyword_map = {
            "杯段": ("league", lambda v: league_map.get(v)),
            "本位": ("townhall", lambda v: v if re.fullmatch(r'\d+,\d+', v) else None),
            "等级": ("exp", lambda v: v if re.fullmatch(r'\d+,\d+', v) else None),
            "奖杯": ("trophies", lambda v: v if re.fullmatch(r'\d+,\d+', v) else None)
        }

        errors = []

        # 提取参数
        for keyword, (param_name, validator) in keyword_map.items():
            match = re.search(rf'{keyword}([^\s]+)', remaining_content)
            if match:
                value = match.group(1)
                validated_value = validator(value)
                if validated_value is not None:
                    params[param_name] = validated_value
                else:
                    errors.append(f"❌ {keyword} 参数值 '{value}' 格式无效或无法识别。")
                    # 可以选择 return 或继续处理其他参数
                    # return wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} {errors[-1]}", msg.roomid, msg.sender)

        # 如果在参数提取过程中发现错误，发送错误信息并返回
        if errors:
            error_message = "\n".join(errors)
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} \n{error_message}", msg.roomid, msg.sender)
            return

        wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在查询玩家 '{player_name}' 的信息，请稍候...", msg.roomid, msg.sender)

        # 使用局部 params 调用 API
        res = self._api.get_data('player_search', params)

        status_code = res.get('status_code')
        content_type = res.get('content_type')
        data = res.get('content')
        error_msg = res.get('error')

        if status_code == 200 and content_type == 'json' and data:
            # 检查 data 是否为字典且包含 'items' 列表
            if isinstance(data, dict) and 'items' in data and isinstance(data['items'], list):
                player_list = data['items']
                if not player_list:
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询成功，但未找到符合条件的玩家。", msg.roomid, msg.sender)
                else:
                    # 提取名称和标签，格式化为文本
                    output_lines = []
                    for player in player_list:
                        # 假设每个 player 字典都有 'name' 和 'tag' 键
                        player_name = player.get('name', '未知名称')
                        player_tag = player.get('tag', '未知标签')
                        output_lines.append(f"名称: {player_name}, 标签: {player_tag}")

                    output_text = "\n".join(output_lines)
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询结果如下：\n{output_text}", msg.roomid, msg.sender)
            else:
                # 如果返回的数据结构不符合预期
                logger.warning(f"Player search API returned unexpected data structure: {data}")
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但返回的数据格式不符合预期（非字典或缺少items列表）。", msg.roomid, msg.sender)
        elif status_code == 403:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ API认证失败，请联系管理员。", msg.roomid, msg.sender)
        elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
                maintenance_message = data.get('message', "API正在维护中，请稍后再试。") # 获取维护信息
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 🚧 {maintenance_message}", msg.roomid, msg.sender)
        elif status_code == 555:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但无法解析返回的数据格式。", msg.roomid, msg.sender)
        else:
            # 其他所有错误情况
            error_detail = f"状态码: {status_code}" if status_code else ""
            if error_msg:
                error_detail += f", 错误: {error_msg}"
            # 检查是否有特定的API错误消息
            api_error_reason = data.get('reason') if isinstance(data, dict) else None
            api_error_message = data.get('message') if isinstance(data, dict) else None
            if api_error_reason:
                error_detail += f", 原因: {api_error_reason}"
            if api_error_message:
                error_detail += f", 信息: {api_error_message}"

            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败。{error_detail}", msg.roomid, msg.sender)

    def player_warhits_mode(self, wcf: Wcf, msg: WxMsg, content: str) -> Optional[str]:
        """查询玩家实力模式"""
        # 从content中提取出村庄标签，以#开头，为数字或字母
        match = re.search(r'(#[a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
        if match:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在查询玩家实力信息并生成图片，请稍候...", msg.roomid, msg.sender)
            self.params['tag'] = match.group(1)  # 提取匹配的村庄标签
            # 生成唯一的文件名
            timestamp = int(time.time())
            filename = f"player_warhits_{self.params['tag']}_{timestamp}.png"
            res = self._api.get_data('player_warhits', self.params)
            status_code = res.get('status_code')
            content_type = res.get('content_type')
            data = res.get('content')
            error_msg = res.get('error')
            if status_code == 200 and content_type == 'json' and data:
                try:
                    pm = PicMaker("player_warhits", data) # 使用正确的 PicMaker 类型
                    img_path = pm.generate(filename)
                    if img_path:
                        wcf.send_image(img_path, msg.roomid)
                    else:
                            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询成功，但图片生成失败。", msg.roomid, msg.sender)
                except Exception as e:
                    logger.error(f"PicMaker failed for player_warhits: {e}")
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 图片生成过程中出错，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 403:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ API认证失败，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
                    maintenance_message = "服务器正在维护中，请稍后再试..."
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 🚧 {maintenance_message}", msg.roomid, msg.sender)
            elif status_code == 555:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但无法解析返回的数据格式。", msg.roomid, msg.sender)
            else:
                # 其他所有错误情况
                error_detail = f"状态码: {status_code}" if status_code else ""
                if error_msg:
                    error_detail += f", 错误: {error_msg}"
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败。{error_detail}", msg.roomid, msg.sender)
        else:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供正确的村庄标签（#开头）。", msg.roomid, msg.sender)

    def player_todo_mode(self, wcf: Wcf, msg: WxMsg, content: str) -> Optional[str]:
        """查询玩家待办事项模式"""
        """查询玩家实力模式"""
        # 从content中提取出村庄标签，以#开头，为数字或字母
        match = re.search(r'(#[a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
        if match:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在查询玩家待办信息并生成图片，请稍候...", msg.roomid, msg.sender)
            self.params['tag'] = match.group(1)  # 提取匹配的村庄标签
            # 生成唯一的文件名
            timestamp = int(time.time())
            filename = f"player_todo_{self.params['tag']}_{timestamp}.png"
            res = self._api.get_data('player_todo', self.params)
            status_code = res.get('status_code')
            content_type = res.get('content_type')
            data = res.get('content')
            error_msg = res.get('error')
            if status_code == 200 and content_type == 'json' and data:
                try:
                    pm = PicMaker("player_todo", data) # 使用正确的 PicMaker 类型
                    img_path = pm.generate(filename)
                    if img_path:
                        wcf.send_image(img_path, msg.roomid)
                    else:
                            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询成功，但图片生成失败。", msg.roomid, msg.sender)
                except Exception as e:
                    logger.error(f"PicMaker failed for player_warhits: {e}")
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 图片生成过程中出错，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 403:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ API认证失败，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
                    maintenance_message = "服务器正在维护中，请稍后再试..."
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 🚧 {maintenance_message}", msg.roomid, msg.sender)
            elif status_code == 555:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但无法解析返回的数据格式。", msg.roomid, msg.sender)
            else:
                # 其他所有错误情况
                error_detail = f"状态码: {status_code}" if status_code else ""
                if error_msg:
                    error_detail += f", 错误: {error_msg}"
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败。{error_detail}", msg.roomid, msg.sender)
        else:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供正确的村庄标签（#开头）。", msg.roomid, msg.sender)
    

    def clan_info_mode(self, wcf: Wcf, msg: WxMsg, content: str) -> Optional[str]:
        """查询部落模式"""
        # 从content中提取出部落标签，以#开头，为数字或字母
        match = re.search(r'(#[a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
        if match:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在查询部落信息并生成图片，请稍候...", msg.roomid, msg.sender)
            self.params['tag'] = match.group(1)  # 提取匹配的部落标签
            # 生成唯一的文件名
            timestamp = int(time.time())
            filename = f"clan_info_{self.params['tag']}_{timestamp}.png"
            res = self._api.get_data('clan_info', self.params) # 修正API模式为 clan_info

            status_code = res.get('status_code')
            content_type = res.get('content_type')
            data = res.get('content')
            error_msg = res.get('error')

            if status_code == 200 and content_type == 'json' and data:
                try:
                    pm = PicMaker("clan_info", data) # 修正 PicMaker 类型
                    img_path = pm.generate(filename)
                    if img_path:
                        wcf.send_image(img_path, msg.roomid)
                    else:
                        wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询成功，但图片生成失败。", msg.roomid, msg.sender)
                except Exception as e:
                    logger.error(f"PicMaker failed for clan_info: {e}")
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 图片生成过程中出错，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 403:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ API认证失败，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
                    maintenance_message = data.get('message', "API正在维护中，请稍后再试。") # 获取维护信息
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 🚧 {maintenance_message}", msg.roomid, msg.sender)
            elif status_code == 555:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但无法解析返回的数据格式。", msg.roomid, msg.sender)
            else:
                # 其他所有错误情况
                error_detail = f"状态码: {status_code}" if status_code else ""
                if error_msg:
                    error_detail += f", 错误: {error_msg}"
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败。{error_detail}", msg.roomid, msg.sender)
        else:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供正确的部落标签（#开头）。", msg.roomid, msg.sender)

    def clan_war_mode(self, wcf: Wcf, msg: WxMsg, content: str) -> Optional[str]:
        """查询部落对战模式"""
        # 从content中提取出部落标签，以#开头，为数字或字母
        match = re.search(r'(#[a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
        if match:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在查询部落对战信息并生成ipv6链接，请稍候...", msg.roomid, msg.sender)
            self.params['tag'] = match.group(1)  # 提取匹配的部落标签
            res = self._api.get_data('clan_war', self.params)
            status_code = res.get('status_code')
            content_type = res.get('content_type')
            data = res.get('content')
            error_msg = res.get('error')

            if status_code == 200 and content_type == 'json' and data:  
                try:
                    pm = PicMaker("clan_war", data) # 修正 PicMaker 类型
                    img_path = pm.generate(filename)
                    if img_path:
                        wcf.send_image(img_path, msg.roomid)
                    else:
                        wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询成功，但图片生成失败。", msg.roomid, msg.sender)
                except Exception as e:
                    logger.error(f"PicMaker failed for clan_war: {e}")
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 图片生成过程中出错，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 403:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ API认证失败，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 503 and content_type == 'json' and data and data.get('reason') == 'inMaintenance':
                    maintenance_message = data.get('message', "API正在维护中，请稍后再试。") # 获取维护信息
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 🚧 {maintenance_message}", msg.roomid, msg.sender)
            elif status_code == 555:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但无法解析返回的数据格式。", msg.roomid, msg.sender)
            else:
                # 其他所有错误情况
                error_detail = f"状态码: {status_code}" if status_code else ""
                if error_msg:
                    error_detail += f", 错误: {error_msg}"
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败。{error_detail}", msg.roomid, msg.sender)
        else:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供正确的部落标签（#开头）。", msg.roomid, msg.sender)

    def clan_raids_mode(self, wcf: Wcf, msg: WxMsg, content: str) -> Optional[str]:
        """查询部落突袭模式"""
        # 从content中提取出部落标签，以#开头，为数字或字母
        match = re.search(r'(#[a-zA-Z0-9]+)', content)  # 使用正则表达式匹配
        if match:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 正在查询部落突袭信息并生成图片，请稍候...", msg.roomid, msg.sender)
            self.params['tag'] = match.group(1)  # 提取匹配的部落标签
            # 生成唯一的文件名
            timestamp = int(time.time())
            filename = f"clan_raids_{self.params['tag']}_{timestamp}.png"
            res_raids = self._api.get_data('clan_raids', self.params) 
            res_members = self._api.get_data('clan_members', self.params)

            status_code = res_raids.get('status_code')
            content_type = res_raids.get('content_type')
            data_raids = res_raids.get('content')
            error_msg = res_raids.get('error')
            data_members = res_members.get('content')
            data = {
                "raids": data_raids.get('items'),
                "members": data_members.get('items')
            }

            if status_code == 200 and content_type == 'json' and data:
                try:
                    pm = PicMaker("clan_raids", data) # 修正 PicMaker 类型
                    img_path = pm.generate(filename)
                    if img_path:
                        wcf.send_image(img_path, msg.roomid)
                    else:
                        wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ✅ 查询成功，但图片生成失败。", msg.roomid, msg.sender)
                except Exception as e:
                    logger.error(f"PicMaker failed for clan_raids: {e}")
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 图片生成过程中出错，请联系管理员。", msg.roomid, msg.sender)    
            elif status_code == 403:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ API认证失败，请联系管理员。", msg.roomid, msg.sender)
            elif status_code == 503 and content_type == 'json' and data_raids and data_raids.get('reason') == 'inMaintenance':
                    maintenance_message = data_raids.get('message', "API正在维护中，请稍后再试。") # 获取维护信息
                    wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} 🚧 {maintenance_message}", msg.roomid, msg.sender) 
            elif status_code == 555:
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 查询成功，但无法解析返回的数据格式。", msg.roomid, msg.sender)
            else:
                # 其他所有错误情况
                error_detail = f"状态码: {status_code}" if status_code else ""
                if error_msg:
                    error_detail += f", 错误: {error_msg}"
                wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请求失败。{error_detail}", msg.roomid, msg.sender)
        else:
            wcf.send_text(f"@{wcf.get_alias_in_chatroom(msg.sender, msg.roomid)} ❌ 请提供正确的部落标签（#开头）。", msg.roomid, msg.sender)
