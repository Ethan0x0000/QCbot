import json
import os
from pathlib import Path

class RoomMonitor:
    """
    RoomMonitor类用于管理用户wxid与个人标签的绑定关系（一对多），以及room_id与部落标签的绑定关系（一对一）
    """
    
    def __init__(self):
        # 用户wxid与个人标签的映射关系 (wxid -> list of tags)
        self.wxid_to_tags = {}  
        self.tag_to_wxid = {}  # 个人标签 -> wxid
        
        # room_id与部落标签的映射关系 (一对一)
        self.room_to_clan_tag = {}  # room_id -> 部落标签
        self.clan_tag_to_room = {}  # 部落标签 -> room_id
        
        # 存储路径
        self.storage_dir = Path(os.getcwd()) / "storage" / "room_monitor"
        self.user_tags_file = self.storage_dir / "user_tags.json"
        self.clan_tags_file = self.storage_dir / "clan_tags.json"
        
        # 确保存储目录存在
        self._ensure_storage_path()
        
        # 加载已有数据
        self._load_data()
    
    def _ensure_storage_path(self):
        """确保存储路径存在"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_data(self):
        """从存储文件加载数据"""
        # 加载用户标签数据
        if self.user_tags_file.exists():
            try:
                with open(self.user_tags_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure backward compatibility: handle old string values
                    loaded_wxid_to_tags = data.get('wxid_to_tags', data.get('wxid_to_tag', {})) # Check for old key too
                    self.wxid_to_tags = {}
                    for w_id, tags_or_tag in loaded_wxid_to_tags.items():
                        if isinstance(tags_or_tag, list):
                            self.wxid_to_tags[w_id] = tags_or_tag
                        elif isinstance(tags_or_tag, str):
                            self.wxid_to_tags[w_id] = [tags_or_tag] # Convert old string format to list
                        else:
                             self.wxid_to_tags[w_id] = [] # Handle unexpected type gracefully
                             
                    self.tag_to_wxid = data.get('tag_to_wxid', {})
            except Exception as e:
                print(f"加载用户标签数据失败: {e}")
                self.wxid_to_tags = {} # Reset on load failure
                self.tag_to_wxid = {}
        
        # 加载部落标签数据 (clan tags are 1-to-1)
        if self.clan_tags_file.exists():
            try:
                with open(self.clan_tags_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.room_to_clan_tag = data.get('room_to_clan_tag', {})
                    self.clan_tag_to_room = data.get('clan_tag_to_room', {})
            except Exception as e:
                print(f"加载部落标签数据失败: {e}")
                self.room_to_clan_tag = {}
                self.clan_tag_to_room = {}
    
    def _save_user_tags(self):
        """保存用户标签数据"""
        try:
            with open(self.user_tags_file, 'w', encoding='utf-8') as f:
                data = {
                    'wxid_to_tags': self.wxid_to_tags, # Use new key name
                    'tag_to_wxid': self.tag_to_wxid
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户标签数据失败: {e}")
    
    def _save_clan_tags(self):
        """保存部落标签数据"""
        try:
            with open(self.clan_tags_file, 'w', encoding='utf-8') as f:
                data = {
                    'room_to_clan_tag': self.room_to_clan_tag,
                    'clan_tag_to_room': self.clan_tag_to_room
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存部落标签数据失败: {e}")
    
    def bind_user_tag(self, wxid, personal_tag):
        """
        绑定用户wxid和个人标签 (一个wxid可以绑定多个标签)
        如果标签已绑定到其他wxid，则解除旧绑定。
        
        Args:
            wxid (str): 用户的wxid
            personal_tag (str): 个人标签，以#开头，由大写字母和数字组成
        
        Returns:
            bool: 绑定是否成功
        """
        # 验证个人标签格式
        if not personal_tag.startswith('#') or not all(c.isdigit() or c.isupper() for c in personal_tag[1:]):
            print(f"无效的个人标签格式: {personal_tag}")
            return False
        
        # 检查此标签是否已绑定到 *其他* wxid
        if personal_tag in self.tag_to_wxid:
            old_wxid = self.tag_to_wxid[personal_tag]
            if old_wxid != wxid:
                # 从旧wxid的标签列表中移除此标签
                if old_wxid in self.wxid_to_tags and personal_tag in self.wxid_to_tags[old_wxid]:
                    self.wxid_to_tags[old_wxid].remove(personal_tag)
                    # 如果旧wxid的标签列表为空，则删除该wxid条目
                    if not self.wxid_to_tags[old_wxid]:
                        del self.wxid_to_tags[old_wxid]
                # 解除旧的 tag -> wxid 映射 (稍后会重新建立)
                del self.tag_to_wxid[personal_tag]
        
        # 初始化wxid的标签列表（如果不存在）
        if wxid not in self.wxid_to_tags:
            self.wxid_to_tags[wxid] = []
            
        # 添加新标签到wxid的列表 (如果尚未存在)
        if personal_tag not in self.wxid_to_tags[wxid]:
            self.wxid_to_tags[wxid].append(personal_tag)
        
        # 更新 tag -> wxid 映射
        self.tag_to_wxid[personal_tag] = wxid
        
        # 保存数据
        self._save_user_tags()
        return True
    
    def get_tag_by_wxid(self, wxid):
        """
        通过wxid查询个人标签 (返回第一个绑定的标签)
        
        Args:
            wxid (str): 用户的wxid
        
        Returns:
            str: 第一个绑定的个人标签，如果不存在则返回None
        """
        tags = self.wxid_to_tags.get(wxid)
        if tags: # Check if list exists and is not empty
            return tags[0]
        return None
        
    def get_all_tags_by_wxid(self, wxid):
        """
        通过wxid查询所有绑定的个人标签
        
        Args:
            wxid (str): 用户的wxid
        
        Returns:
            list: 包含所有个人标签的列表，如果不存在则返回空列表
        """
        return self.wxid_to_tags.get(wxid, [])

    def get_wxid_by_tag(self, personal_tag):
        """
        通过个人标签查询wxid
        
        Args:
            personal_tag (str): 个人标签
        
        Returns:
            str: 用户的wxid，如果不存在则返回None
        """
        return self.tag_to_wxid.get(personal_tag)
    
    def bind_clan_tag(self, room_id, clan_tag):
        """
        绑定room_id和部落标签 (一对一)
        
        Args:
            room_id (str): 房间ID
            clan_tag (str): 部落标签
        
        Returns:
            bool: 绑定是否成功
        """
        # 如果room_id已经绑定了其他部落标签，先解除旧绑定
        if room_id in self.room_to_clan_tag:
            old_tag = self.room_to_clan_tag[room_id]
            if old_tag in self.clan_tag_to_room:
                del self.clan_tag_to_room[old_tag]
        
        # 如果部落标签已经绑定了其他room_id，先解除旧绑定
        if clan_tag in self.clan_tag_to_room:
            old_room = self.clan_tag_to_room[clan_tag]
            if old_room in self.room_to_clan_tag:
                del self.room_to_clan_tag[old_room]
        
        # 建立新的绑定关系
        self.room_to_clan_tag[room_id] = clan_tag
        self.clan_tag_to_room[clan_tag] = room_id
        
        # 保存数据
        self._save_clan_tags()
        return True
    
    def get_clan_tag_by_room(self, room_id):
        """
        通过room_id查询部落标签
        
        Args:
            room_id (str): 房间ID
        
        Returns:
            str: 部落标签，如果不存在则返回None
        """
        return self.room_to_clan_tag.get(room_id)
    
    def get_room_by_clan_tag(self, clan_tag):
        """
        通过部落标签查询room_id
        
        Args:
            clan_tag (str): 部落标签
        
        Returns:
            str: 房间ID，如果不存在则返回None
        """
        return self.clan_tag_to_room.get(clan_tag)
    
    def unbind_user_tag(self, wxid=None, personal_tag=None):
        """
        解除用户wxid和个人标签的绑定关系。
        - 提供wxid时，解除该wxid绑定的所有标签。
        - 提供personal_tag时，解除该特定标签的绑定。
        
        Args:
            wxid (str, optional): 用户的wxid
            personal_tag (str, optional): 个人标签
            
        Note:
            至少提供wxid或personal_tag中的一个参数
            
        Returns:
            bool: 解除绑定是否成功
        """
        if wxid is None and personal_tag is None:
            print("解绑用户标签需要提供wxid或personal_tag")
            return False
            
        success = False
        
        # 通过wxid解绑 (删除wxid及其所有关联标签)
        if wxid is not None and wxid in self.wxid_to_tags:
            tags_to_remove = self.wxid_to_tags[wxid][:] # Copy list before iterating
            for tag in tags_to_remove:
                if tag in self.tag_to_wxid:
                    del self.tag_to_wxid[tag]
            del self.wxid_to_tags[wxid]
            success = True
            
        # 通过personal_tag解绑 (仅删除此标签)
        if personal_tag is not None and personal_tag in self.tag_to_wxid:
            user_id = self.tag_to_wxid[personal_tag]
            del self.tag_to_wxid[personal_tag] # Remove tag -> wxid link
            
            if user_id in self.wxid_to_tags:
                if personal_tag in self.wxid_to_tags[user_id]:
                    self.wxid_to_tags[user_id].remove(personal_tag)
                # 如果移除后列表为空，删除wxid条目
                if not self.wxid_to_tags[user_id]:
                    del self.wxid_to_tags[user_id]
            success = True # Even if wxid was already gone, tag->wxid link was removed
            
        # 保存更新后的数据
        if success:
            self._save_user_tags()
            
        return success
    
    def unbind_clan_tag(self, room_id=None, clan_tag=None):
        """
        解除room_id和部落标签的绑定关系 (一对一)
        
        Args:
            room_id (str, optional): 房间ID
            clan_tag (str, optional): 部落标签
            
        Note:
            必须提供room_id或clan_tag中的一个参数
            
        Returns:
            bool: 解除绑定是否成功
        """
        if room_id is None and clan_tag is None:
            print("解绑部落标签需要提供room_id或clan_tag")
            return False
            
        success = False
        
        # 如果提供了room_id，通过room_id解除绑定
        if room_id is not None and room_id in self.room_to_clan_tag:
            tag = self.room_to_clan_tag[room_id]
            del self.room_to_clan_tag[room_id]
            if tag in self.clan_tag_to_room:
                del self.clan_tag_to_room[tag]
            success = True
            
        # 如果提供了clan_tag，通过标签解除绑定
        if clan_tag is not None and clan_tag in self.clan_tag_to_room:
            room = self.clan_tag_to_room[clan_tag]
            del self.clan_tag_to_room[clan_tag]
            if room in self.room_to_clan_tag:
                del self.room_to_clan_tag[room]
            success = True
            
        # 保存更新后的数据
        if success:
            self._save_clan_tags()
            
        return success
    

if __name__ == "__main__":
    room_monitor = RoomMonitor()
    room_monitor.bind_user_tag("wxid_1234567890", "#A1")
    room_monitor.bind_user_tag("wxid_1234567890", "#A2")
    room_monitor.bind_clan_tag("room_1234567890", "#A1")
    print(room_monitor.get_tag_by_wxid("wxid_1234567890"))
    print(room_monitor.get_clan_tag_by_room("room_1234567890"))

