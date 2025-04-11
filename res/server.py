from flask import Flask, send_from_directory
import os
import socket

app = Flask(__name__)

# 获取当前文件夹路径
current_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    # 默认返回 index.html
    return send_from_directory(current_dir, 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    # 检查文件是否存在且是HTML文件
    if filename.endswith('.html') and os.path.exists(os.path.join(current_dir, filename)):
        return send_from_directory(current_dir, filename)
    return "File not found", 404

if __name__ == '__main__':
    # 同时支持IPv4和IPv6
    host = '::'  # 监听所有IPv6接口，同时兼容IPv4
    port = 5000
    
    # 检查IPv6支持
    try:
        socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        print(f"服务器将在 [{host}]:{port} 启动")
    except Exception as e:
        print(f"IPv6支持检查失败: {e}")
        host = '0.0.0.0'  # 回退到IPv4
        print(f"将使用IPv4地址 {host}:{port}")
    
    app.run(host=host, port=port, debug=True)