import os
import json
import time
import logging
import threading
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

class PicMaker:
    """
    图片生成类，用于根据不同需求绘制图片
    
    支持不同的缓存等级：
    - 0: 10秒寿命，超过自动删除
    - 1: 5分钟寿命，超过自动删除
    - 100: 永久寿命，不会自动删除
    """
    
    def __init__(self, mode: str, data: Union[Dict[str, Any], str], cache_level: Optional[int] = None):
        """
        初始化图片生成器
        
        Args:
            mode: 生成模式，决定如何处理和绘制图片
            data: JSON数据，可以是字典或JSON字符串
            cache_level: 缓存等级（可选），如果不指定则根据mode自动确定
                0 - 10秒寿命
                1 - 5分钟寿命
                100 - 永久寿命
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
        
        # 根据mode自动确定缓存等级，或使用传入的cache_level
        if cache_level is None:
            # 根据不同模式设置缓存等级
            if self.mode == "simple":
                self.cache_level = 0  # 简单模式使用10秒缓存
            elif self.mode == "chart":
                self.cache_level = 1  # 图表模式使用5分钟缓存
            elif self.mode == "complex":
                self.cache_level = 100  # 复杂模式使用永久缓存
            else:
                self.cache_level = 1  # 默认模式使用5分钟缓存
            self.logger.info(f"根据模式 {self.mode} 自动设置缓存等级为 {self.cache_level}")
        elif cache_level not in [0, 1, 100]:
            self.logger.warning(f"无效的缓存等级 {cache_level}，使用默认值 1")
            self.cache_level = 1
        else:
            self.cache_level = cache_level
            self.logger.info(f"使用手动指定的缓存等级: {self.cache_level}")
        
        # 缓存目录
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage', 'images')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 缓存清理线程
        self.cache_cleaner = None
        if self.cache_level != 100:  # 非永久缓存才需要清理
            self.start_cache_cleaner()
        
        self.logger.info(f"PicMaker初始化完成: 模式={mode}, 缓存等级={self.cache_level}")
    
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
            
            # 记录缓存信息
            self._record_cache_info(filepath)
            
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
    
    def _record_cache_info(self, filepath: str) -> None:
        """
        记录缓存信息
        
        Args:
            filepath: 图片文件路径
        """
        # 计算过期时间
        if self.cache_level == 0:
            expiry_time = datetime.now() + timedelta(seconds=10)
        elif self.cache_level == 1:
            expiry_time = datetime.now() + timedelta(minutes=5)
        else:  # cache_level == 100
            expiry_time = None
        
        # 创建缓存信息文件
        if expiry_time:
            cache_info_path = f"{filepath}.cache_info"
            with open(cache_info_path, 'w') as f:
                json.dump({
                    'filepath': filepath,
                    'expiry_time': expiry_time.isoformat() if expiry_time else None,
                    'cache_level': self.cache_level
                }, f)
    
    def start_cache_cleaner(self) -> None:
        """
        启动缓存清理线程
        """
        if self.cache_cleaner and self.cache_cleaner.is_alive():
            return
        
        self.cache_cleaner = threading.Thread(target=self._clean_cache, daemon=True)
        self.cache_cleaner.start()
        self.logger.info("缓存清理线程已启动")
    
    def _clean_cache(self) -> None:
        """
        清理过期的缓存文件
        """
        while True:
            try:
                now = datetime.now()
                
                # 遍历缓存目录
                for filename in os.listdir(self.cache_dir):
                    if filename.endswith('.cache_info'):
                        cache_info_path = os.path.join(self.cache_dir, filename)
                        
                        try:
                            # 读取缓存信息
                            with open(cache_info_path, 'r') as f:
                                cache_info = json.load(f)
                            
                            # 检查是否过期
                            if 'expiry_time' in cache_info and cache_info['expiry_time']:
                                expiry_time = datetime.fromisoformat(cache_info['expiry_time'])
                                
                                if now > expiry_time:
                                    # 删除图片文件
                                    image_path = cache_info['filepath']
                                    if os.path.exists(image_path):
                                        os.remove(image_path)
                                        self.logger.debug(f"已删除过期图片: {image_path}")
                                    
                                    # 删除缓存信息文件
                                    os.remove(cache_info_path)
                                    self.logger.debug(f"已删除缓存信息: {cache_info_path}")
                        
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            self.logger.error(f"处理缓存信息文件失败: {cache_info_path}, 错误: {str(e)}")
                            # 删除损坏的缓存信息文件
                            os.remove(cache_info_path)
            
            except Exception as e:
                self.logger.error(f"缓存清理过程中发生错误: {str(e)}")
            
            # 根据缓存等级设置检查间隔
            if self.cache_level == 0:  # 10秒寿命
                time.sleep(2)  # 每2秒检查一次
            else:  # 5分钟寿命
                time.sleep(30)  # 每30秒检查一次