#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import time
import base64
import cgi
import requests
import PyPDF2
import cv2
import fitz  # PyMuPDF
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

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

def save_courses(data):
    """保存课程数据"""
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_files():
    """获取文件列表"""
    with open(FILES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_files(data):
    """保存文件数据"""
    with open(FILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_note_cards(course_id=None):
    """获取笔记卡片"""
    with open(NOTE_CARDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        cards = data.get("cards", [])
        if course_id:
            cards = [card for card in cards if card.get("course_id") == course_id]
        return cards

def save_note_cards(cards):
    """保存笔记卡片"""
    with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"cards": cards}, f, ensure_ascii=False, indent=2)

def delete_note_card(card_id):
    """删除笔记卡片"""
    try:
        cards = get_note_cards()
        card_to_delete = None
        
        # 找到要删除的卡片
        for card in cards:
            if card["id"] == card_id:
                card_to_delete = card
                break
        
        if not card_to_delete:
            return {"success": False, "error": "卡片不存在"}
        
        # 删除关联的图片文件
        if card_to_delete.get("image"):
            image_path = os.path.join(UPLOAD_DIR, card_to_delete["image"].lstrip('/uploads/'))
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    print(f"删除图片文件失败: {str(e)}")
        
        # 从列表中移除卡片
        cards = [card for card in cards if card["id"] != card_id]
        save_note_cards(cards)
        
        return {"success": True, "message": "卡片删除成功"}
        
    except Exception as e:
        return {"success": False, "error": f"删除卡片失败: {str(e)}"}

def update_note_card(card_id, title, content):
    """更新笔记卡片"""
    try:
        cards = get_note_cards()
        
        # 找到要更新的卡片
        for card in cards:
            if card["id"] == card_id:
                card["title"] = title
                card["content"] = content
                break
        else:
            return {"success": False, "error": "卡片不存在"}
        
        save_note_cards(cards)
        return {"success": True, "message": "卡片更新成功"}
        
    except Exception as e:
        return {"success": False, "error": f"更新卡片失败: {str(e)}"}

def get_course(course_id):
    """根据ID获取课程"""
    courses_data = get_courses()
    for course in courses_data["courses"]:
        if course["id"] == course_id:
            return course
    return None

def create_course(name):
    """创建新课程"""
    courses_data = get_courses()
    new_course = {
        "id": str(uuid.uuid4()),
        "name": name,
        "created_at": time.time()
    }
    courses_data["courses"].append(new_course)
    save_courses(courses_data)
    return new_course

def get_course_files(course_id):
    """获取课程的所有文件"""
    files_data = get_files()
    return [file for file in files_data["files"] if file["course_id"] == course_id]

def add_file_record(file_name, file_type, file_path, course_id, summary="", screenshots=None):
    """添加文件记录"""
    files_data = get_files()
    new_file = {
        "id": str(uuid.uuid4()),
        "name": file_name,
        "type": file_type,
        "path": file_path,
        "course_id": course_id,
        "summary": summary,
        "uploaded_at": time.time(),
        "screenshots": screenshots or []
    }
    files_data["files"].append(new_file)
    save_files(files_data)
    return new_file

def delete_file(file_id, course_id):
    """删除文件"""
    try:
        files_data = get_files()
        file_to_delete = None
        
        # 找到要删除的文件
        for file in files_data["files"]:
            if file["id"] == file_id and file["course_id"] == course_id:
                file_to_delete = file
                break
        
        if not file_to_delete:
            return {"success": False, "error": "文件不存在"}
        
        # 删除物理文件
        file_path = os.path.join(UPLOAD_DIR, file_to_delete["path"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除物理文件失败: {str(e)}")
        
        # 删除截图文件
        if file_to_delete.get("screenshots"):
            for screenshot in file_to_delete["screenshots"]:
                screenshot_path = os.path.join(UPLOAD_DIR, screenshot.lstrip('/uploads/'))
                if os.path.exists(screenshot_path):
                    try:
                        os.remove(screenshot_path)
                    except Exception as e:
                        print(f"删除截图文件失败: {str(e)}")
        
        # 从列表中移除文件记录
        files_data["files"] = [file for file in files_data["files"] if file["id"] != file_id]
        save_files(files_data)
        
        return {"success": True, "message": "文件删除成功"}
        
    except Exception as e:
        return {"success": False, "error": f"删除文件失败: {str(e)}"}

class SimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # 处理静态文件请求（图片等）
        if self.path.startswith('/uploads/'):
            try:
                # 构建文件路径
                file_path = os.path.join(UPLOAD_DIR, self.path[9:])  # 去掉 '/uploads/' 前缀
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    # 确定文件类型
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        content_type = 'image/png' if file_path.lower().endswith('.png') else 'image/jpeg'
                    else:
                        content_type = 'application/octet-stream'
                    
                    # 发送文件
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-type', content_type)
                    self.end_headers()
                    
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                else:
                    self.send_response(404)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(b'File Not Found')
                    return
            except Exception as e:
                print(f"静态文件服务错误: {str(e)}")
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'Internal Server Error')
                return
        
        # API请求处理
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 获取课程列表
        if self.path == '/api/courses':
            self.wfile.write(json.dumps(get_courses()).encode('utf-8'))
            
        # 获取课程文件
        elif self.path.startswith('/api/courses/') and '/files' in self.path:
            parts = self.path.split('/')
            course_id = parts[3]  # /api/courses/{course_id}/files
            course_files = get_course_files(course_id)
            self.wfile.write(json.dumps({"files": course_files}).encode('utf-8'))
            
        # 获取课程笔记卡片
        elif self.path.startswith('/api/courses/') and '/cards' in self.path:
            parts = self.path.split('/')
            course_id = parts[3]  # /api/courses/{course_id}/cards
            cards = get_note_cards(course_id)
            self.wfile.write(json.dumps({"cards": cards}).encode('utf-8'))
            
        else:
            self.wfile.write(json.dumps({
                "error": "路径不存在"
            }).encode('utf-8'))
    
    def call_google_ai_api(self, prompt):
        """调用Google AI API处理文本请求"""
        try:
            # 获取API密钥
            api_key = os.getenv('GOOGLE_AI_API_KEY')
            
            if not api_key:
                return "错误: 未设置Google AI API密钥。请在.env文件中配置GOOGLE_AI_API_KEY。"
            
            # 使用gemini-2.0-flash模型（2024年最新）
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 2048
                }
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                
                return "AI未能生成有效回复"
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_details = error_json["error"]["message"]
                except:
                    pass
                
                return f"API调用失败: HTTP {response.status_code}\n{error_details}"
            
        except Exception as e:
            return f"处理请求时出错: {str(e)}"
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 创建新课程
        if self.path == '/api/courses':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', '').strip()
                
                if not name:
                    self.wfile.write(json.dumps({
                        "error": "课程名称不能为空"
                    }).encode('utf-8'))
                    return
                
                new_course = create_course(name)
                self.wfile.write(json.dumps({
                    "course": new_course
                }).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"创建课程失败: {str(e)}"
                }).encode('utf-8'))
        
        # 聊天功能
        elif self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                
                if not message.strip():
                    self.wfile.write(json.dumps({
                        "error": "消息不能为空"
                    }).encode('utf-8'))
                    return
                
                # 调用AI接口
                ai_response = self.call_google_ai_api(message)
                
                self.wfile.write(json.dumps({
                    "response": ai_response
                }).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": str(e)
                }).encode('utf-8'))
        
        else:
            self.wfile.write(json.dumps({
                "error": "路径不存在"
            }).encode('utf-8'))
    
    def do_DELETE(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 删除笔记卡片
        if self.path.startswith('/api/cards/'):
            # 解析URL: /api/cards/{card_id}
            parts = self.path.split('/')
            if len(parts) >= 3:
                card_id = parts[3]
                
                try:
                    result = delete_note_card(card_id)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                    
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "error": "无效的删除请求路径"
                }).encode('utf-8'))
        
        else:
            self.wfile.write(json.dumps({
                "error": "不支持的请求地址"
            }).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    init_data_files()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'启动服务器在端口 {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run() 