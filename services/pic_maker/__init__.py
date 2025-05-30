import os
from pathlib import Path
import json
import time
import logging
from typing import Dict, Any, Union

class PicMaker:
    """
    图片生成类，用于根据不同需求绘制图片
    """
    
    def __init__(self, mode: str, data: Union[Dict[str, Any], str]):
        """
        初始化图片生成器
        
        Args:
            mode: 生成模式，决定如何处理和绘制图片
            data: JSON数据，可以是字典或JSON字符串
        """
        self.logger = logging.getLogger('PicMaker')
        self.logger.setLevel(logging.INFO)
        
        
        self.mode = mode
        
        # 确保data是字典类型
        if isinstance(data, str):
            try:
                self.data = json.loads(data)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {str(e)}")
                raise ValueError(f"提供的数据不是有效的JSON格式: {str(e)}")
        else:
            self.data = data
        
        # 缓存目录
        self.cache_dir = Path(__file__).parent.parent.parent / "storage/cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.logger.info(f"PicMaker初始化完成: 模式={mode}")
    
    def generate(self, filename: str) -> str:
        """
        根据指定的模式和数据生成图片
        
        Returns:
            生成的图片路径
        """
        self.logger.info(f"开始生成图片, 模式: {self.mode}")
        
        # 生成唯一的文件名
        filepath = os.path.join(self.cache_dir, filename)
        
        try:
            # 根据不同模式生成图片
            if self.mode == "player_info":
                self._generate_player_info(filepath)
            elif self.mode == "player_legend":
                self._generate_player_legend(filepath)
            elif self.mode == "player_warhits":
                self._generate_player_warhits(filepath)
            elif self.mode == "player_todo":
                self._generate_player_todo(filepath)
            elif self.mode == "clan_info":
                self._generate_clan_info(filepath)
            elif self.mode == "clan_raids":
                self._generate_clan_raids(filepath)
            else:
                self.logger.warning(f"未知的生成模式: {self.mode}，使用默认模式")
                pass
            
            self.logger.info(f"图片生成成功: {filename}")
            return filepath
        
        except Exception as e:
            self.logger.error(f"图片生成失败: {str(e)}")
            raise RuntimeError(f"图片生成失败: {str(e)}")
    
    def _generate_player_info(self, filepath: str) -> None:
        """
        生成玩家统计图片
        
        Args:
            filepath: 图片保存路径
        """
        from .player_info import generate_player_info_image
        # 调用player_info.py中的函数生成图片
        generate_player_info_image(self.data, filepath)
    
    def _generate_player_legend(self, filepath: str) -> None:
        """
        生成玩家联赛图片
        
        Args:
            filepath: 图片保存路径
        """
        from .player_legend import generate_player_legend_image
        # 调用player_legend.py中的函数生成图片
        generate_player_legend_image(self.data, filepath)

    def _generate_player_warhits(self, filepath: str) -> None:
        """
        生成玩家实力图片

        Args:
            filepath: 图片保存路径
        """
        from.player_warhits import generate_player_warhits_image
        # 调用player_warhits.py中的函数生成图片
        generate_player_warhits_image(self.data, filepath)

    def _generate_player_todo(self, filepath: str) -> None:
        """
        生成玩家待办事项图片
        """
        from .player_todo import generate_player_todo_image
        # 调用player_todo.py中的函数生成图片
        generate_player_todo_image(self.data, filepath)

    def _generate_clan_info(self, filepath: str) -> None:
        """
        生成部落信息图片
        
        Args:
            filepath: 图片保存路径
        """
        from .clan_info import generate_clan_info_image
        # 调用clan_info.py中的函数生成图片
        generate_clan_info_image(self.data, filepath)

    def _generate_clan_raids(self, filepath: str) -> None:
        """
        生成部落突袭图片
        """
        from .clan_raids import generate_clan_raids_image
        # 调用clan_raids.py中的函数生成图片
        generate_clan_raids_image(self.data, filepath)