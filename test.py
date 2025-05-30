import requests
import json

def send_text_message(api, robot_wxid, from_wxid, msg):
    """
    发送文本消息
    
    参数:
        api (str): API代码
        robot_wxid (str): 机器人的wxid
        from_wxid (str): 目标id
        msg (str): 消息内容
    """
    # 接口URL
    url = "http://192.168.2.183:2022/KP"
    
    # 请求头
    headers = {
        "Content-Type": "application/json"
    }
    
    # 请求数据
    data = {
        "api": api,
        "robotWxid": robot_wxid,
        "fromWxid": from_wxid,
        "msg": msg
    }
    
    try:
        # 发送POST请求
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        # 打印响应结果
        print("响应状态码:", response.status_code)
        print("响应内容:", response.text)
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print("JSON响应:", json_response)
        except ValueError:
            print("响应不是有效的JSON格式")
            
    except requests.exceptions.RequestException as e:
        print("请求发生错误:", e)

if __name__ == "__main__":
    # 示例使用
    api_code = "K10033"  # API代码
    bot_wxid = "wxid_m7x1a4e9sf6229"  # 替换为实际的机器人wxid
    target_wxid = "wxid_5r6dy9lyw9yk22"  # 替换为实际的目标wxid
    message = "这是一条测试消息"  # 要发送的消息内容
    
    print("开始发送文本消息...")
    send_text_message(api_code, bot_wxid, target_wxid, message)