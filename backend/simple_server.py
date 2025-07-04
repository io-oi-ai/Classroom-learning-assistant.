#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

# 设置上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 数据文件路径
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
FILES_FILE = os.path.join(DATA_DIR, 'files.json')
NOTE_CARDS_FILE = os.path.join(DATA_DIR, 'note_cards.json')

def init_data_files():
    """初始化数据文件"""
    if not os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"courses": []}, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(FILES_FILE):
        with open(FILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"files": []}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(NOTE_CARDS_FILE):
        with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"cards": []}, f, ensure_ascii=False, indent=2)

def get_courses():
    """获取课程列表"""
    with open(COURSES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

class SimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/api/courses':
            self.wfile.write(json.dumps(get_courses()).encode('utf-8'))
        else:
            self.wfile.write(json.dumps({
                "message": "AI课堂助手后端服务正在运行",
                "status": "ok"
            }).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8001):
    init_data_files()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'🚀 AI课堂助手后端服务启动成功')
    print(f'📍 服务地址: http://localhost:{port}')
    print(f'✅ 服务状态: 正常运行')
    httpd.serve_forever()

if __name__ == '__main__':
    run() 