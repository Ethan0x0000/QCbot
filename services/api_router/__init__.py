import requests
from typing import Dict, Any, Optional
from urllib.parse import quote
import json
import logging
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class APIRouter:
    """
    API 路由器，用于请求 ClashOfClans 和 ClashKing 各种接口
    """
    
    BASE_URL_CK = "https://api.clashk.ing"
    BASE_URL_COC = "https://api.clashofclans.com/v1"

    def __init__(self, timeout: int = None):
        """
        初始化 API Router 客户端
        
        Args:
            timeout: 请求超时时间（秒），如果为None则从环境变量获取
        """
        # 从环境变量获取API token
        self.token = os.getenv('COC_API_TOKEN')
        if not self.token:
            self.logger.error("COC_API_TOKEN环境变量未设置，请检查.env文件")
            raise ValueError("COC_API_TOKEN环境变量未设置")
            
        # 从环境变量获取超时设置，如果未指定则使用参数值或默认值
        self.timeout = timeout if timeout is not None else int(os.getenv('API_TIMEOUT', 30))
        self.session = requests.Session()
        self.logger = logging.getLogger('APIRouter')
        self.logger.setLevel(logging.INFO)
        
    
    def _build_url(self, mode:str, params: Optional[Dict[str, Any]] = None) -> tuple[str, str] :
        """
        构建完整的请求URL
        
        Args:
            mode: API 请求模式
            params: 请求参数，将根据情况插入到URL中
            
        Returns:
            完整的请求URL
        """
        if not isinstance(params, dict):
            raise ValueError("params must be a dictionary")

        match mode:
            case "player_stats":
                return f"{self.BASE_URL_COC}/players/{quote(params['tag'])}", 'coc'
            case "player_lengends":
                return f"{self.BASE_URL_CK}/player/{quote(params['tag'])}/legends", 'ck'
            case "player_search":
                return f"{self.BASE_URL_CK}/player/full-search/{quote(params['name'])}?limit=25", 'ck'
            case "clan_basic":
                return f"{self.BASE_URL_CK}/clan/{quote(params['tag'])}/basic", 'ck'
            case "clan_war":
                return f"{self.BASE_URL_CK}/timeline/{quote(params['tag'])}", 'ck'
            case "clan_leagues":
                return f"{self.BASE_URL_CK}/cwl/{quote(params['tag'])}/{params['season']}", 'ck'
            case "capital_logs":
                return f"{self.BASE_URL_CK}/capital/{quote(params['tag'])}?limit=1", 'ck'
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
        url, target = self._build_url(mode, params)
        
        # 记录请求开始
        self.logger.info(f"开始请求: {url}")
        
        try:
            if target == 'ck':
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                }
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': '*/*',
                    'Connection': 'keep-alive',
                    'Authorization': f'Bearer {self.token}'
                }
            response = self.session.get(url, timeout=self.timeout, headers=headers, verify=True)
            response.raise_for_status()

            
            # 记录成功响应
            self.logger.info(f"请求成功: {url} - 状态码: {response.status_code}")
            
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
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
            elif 'text/html' in content_type:
                self.logger.debug(f"收到HTML响应: {url}")
                # 手动处理响应内容编码
                content = response.content
                try:
                    # 尝试直接解码为utf-8
                    html_content = content.decode('utf-8')
                except UnicodeDecodeError:
                    # 如果失败，尝试检测编码
                    import chardet
                    encoding = chardet.detect(content)['encoding']
                    try:
                        html_content = content.decode(encoding)
                    except:
                        # 如果仍然失败，使用replace模式
                        html_content = content.decode('utf-8', errors='replace')
                
                return {
                    'content_type': 'text/html',
                    'content': html_content
                }
            else:
                self.logger.warning(f"未知的Content-Type: {content_type}")
                return {
                    'content_type': content_type,
                    'content': response.text
                }
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {url} - 错误: {str(e)}")
            raise ValueError(
                f"API 请求失败\n"
                f"URL: {url}\n"
                f"错误详情: {str(e)}"
            ) from e
    
    def get_data(self, mode: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
