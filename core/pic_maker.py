import os
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
        
        # 添加日志处理器（如果尚未添加）
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
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
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage', 'images')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.logger.info(f"PicMaker初始化完成: 模式={mode}")
    
    def generate(self) -> str:
        """
        根据指定的模式和数据生成图片
        
        Returns:
            生成的图片路径
        """
        self.logger.info(f"开始生成图片: 模式={self.mode}")
        
        # 生成唯一的文件名
        timestamp = int(time.time())
        filename = f"{self.mode}_{timestamp}.png"
        filepath = os.path.join(self.cache_dir, filename)
        
        try:
            # 根据不同模式生成图片
            if self.mode == "simple":
                self._generate_simple_image(filepath)
            elif self.mode == "chart":
                self._generate_chart_image(filepath)
            elif self.mode == "complex":
                self._generate_complex_image(filepath)
            else:
                self.logger.warning(f"未知的生成模式: {self.mode}，使用默认模式")
                self._generate_default_image(filepath)
            
            self.logger.info(f"图片生成成功: {filepath}")
            return filepath
        
        except Exception as e:
            self.logger.error(f"图片生成失败: {str(e)}")
            raise RuntimeError(f"图片生成失败: {str(e)}")
    
    def _generate_simple_image(self, filepath: str) -> None:
        """
        生成简单图片
        
        Args:
            filepath: 图片保存路径
        """
        # 这里实现简单图片生成逻辑
        # 示例代码，实际应用中需要替换为真实的图片生成代码
        with open(filepath, 'w') as f:
            f.write("Simple image placeholder")
    
    def _generate_chart_image(self, filepath: str) -> None:
        """
        生成图表图片
        
        Args:
            filepath: 图片保存路径
        """
        # 这里实现图表图片生成逻辑
        # 示例代码，实际应用中需要替换为真实的图片生成代码
        with open(filepath, 'w') as f:
            f.write("Chart image placeholder")
    
    def _generate_complex_image(self, filepath: str) -> None:
        """
        生成复杂图片
        
        Args:
            filepath: 图片保存路径
        """
        # 这里实现复杂图片生成逻辑
        # 示例代码，实际应用中需要替换为真实的图片生成代码
        with open(filepath, 'w') as f:
            f.write("Complex image placeholder")
    
    def _generate_default_image(self, filepath: str) -> None:
        """
        生成默认图片
        
        Args:
            filepath: 图片保存路径
        """
        # 这里实现默认图片生成逻辑
        # 示例代码，实际应用中需要替换为真实的图片生成代码
        with open(filepath, 'w') as f:
            f.write("Default image placeholder")