import requests
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode
import json
import logging

class ClashKing:
    """
    ClashKing API 客户端，用于请求 https://api.clashk.ing/ 各种接口
    """
    
    BASE_URL = "https://api.clashk.ing"
    
    def __init__(self, timeout: int = 30):
        """
        初始化 ClashKing API 客户端
        
        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = logging.getLogger('ClashKingAPI')
        self.logger.setLevel(logging.INFO)
        
        # 添加日志处理器（如果尚未添加）
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _build_url(self, mode:str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        构建完整的请求URL
        
        Args:
            mode: API 请求模式
            params: 请求参数，将根据情况插入到URL中
            
        Returns:
            完整的请求URL
        """
        match mode:
            case "player_stats":
                return f"{self.BASE_URL}/player/{urlencode(params['tag'])}/stats"
            case "player_lengends":
                return f"{self.BASE_URL}/player/{urlencode(params['tag'])}/legends"
            case "player_search":
                return f"{self.BASE_URL}/player/full-search/{urlencode(params['name'])}?limit=25"
            case "clan_basic":
                return f"{self.BASE_URL}/clan/{urlencode(params['tag'])}"
            case "clan_war":
                return f"{self.BASE_URL}/timeline/{urlencode(params['tag'])}"
            case "clan_leagues":
                return f"{self.BASE_URL}/cwl/{urlencode(params['tag'])}/{params['season']}"
            case "capital_logs":
                return f"{self.BASE_URL}/capital/{urlencode(params['tag'])}?limit=1"
            case _:
                raise ValueError("Invalid request mode.")

    
    def _make_request(self, mode: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送 GET 请求到指定的 API 端点
        
        Args:
            mode: API 请求模式
            params: 请求参数，将直接拼接到URL中
            
        Returns:
            API 返回的 JSON 数据
        """
        url = self._build_url(mode, params)
        
        # 记录请求开始
        self.logger.info(f"开始请求: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 记录成功响应
            self.logger.info(f"请求成功: {url} - 状态码: {response.status_code}")
            
            try:
                data = response.json()
                # 可选: 记录响应数据摘要
                self.logger.debug(f"响应数据: {str(data)[:200]}...")
                return data
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {url} - 响应内容: {response.text[:200]}...")
                raise ValueError(
                    f"API 返回的数据不是有效的 JSON 格式\n"
                    f"URL: {url}\n"
                    f"状态码: {response.status_code}\n"
                    f"响应头: {response.headers}\n"
                    f"响应内容: {response.text[:500]}..."
                ) from e
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {url} - 错误: {str(e)}")
            raise ValueError(
                f"API 请求失败\n"
                f"URL: {url}\n"
                f"错误详情: {str(e)}"
            ) from e
    
    def get_data(self, mode: str, **params) -> Dict[str, Any]:
        """
        获取指定端点的数据
        
        Args:
            endpoint: API 端点路径
            **params: 请求参数
            
        Returns:
            API 返回的数据
        """
        return self._make_request(mode, params)
    
    def close(self):
        """
        关闭会话
        """
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()