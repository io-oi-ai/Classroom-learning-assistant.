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
import textwrap
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
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

def delete_course(course_id):
    """删除课程及其所有相关文件"""
    try:
        courses_data = get_courses()
        course_to_delete = None
        
        # 找到要删除的课程
        for course in courses_data["courses"]:
            if course["id"] == course_id:
                course_to_delete = course
                break
        
        if not course_to_delete:
            return {"success": False, "error": "课程不存在"}
        
        # 删除课程相关的所有文件
        course_files = get_course_files(course_id)
        for file in course_files:
            delete_file(file["id"], course_id)
        
        # 删除课程相关的所有笔记卡片
        cards = get_note_cards(course_id)
        for card in cards:
            delete_note_card(card["id"])
        
        # 删除课程目录
        course_dir = os.path.join(UPLOAD_DIR, course_id)
        if os.path.exists(course_dir):
            import shutil
            try:
                shutil.rmtree(course_dir)
            except Exception as e:
                print(f"删除课程目录失败: {str(e)}")
        
        # 从课程列表中移除
        courses_data["courses"] = [c for c in courses_data["courses"] if c["id"] != course_id]
        save_courses(courses_data)
        
        return {"success": True, "message": "课程删除成功"}
        
    except Exception as e:
        return {"success": False, "error": f"删除课程失败: {str(e)}"}

def update_course(course_id, name):
    """更新课程名称"""
    try:
        courses_data = get_courses()
        
        # 找到要更新的课程
        for course in courses_data["courses"]:
            if course["id"] == course_id:
                course["name"] = name.strip()
                save_courses(courses_data)
                return {"success": True, "course": course, "message": "课程名称更新成功"}
        
        return {"success": False, "error": "课程不存在"}
        
    except Exception as e:
        return {"success": False, "error": f"更新课程失败: {str(e)}"}

def get_course_files(course_id):
    """获取课程的所有文件"""
    files_data = get_files()
    result = []
    for file in files_data["files"]:
        # 安全地检查课程ID，支持两种字段名
        file_course_id = file.get("course_id") or file.get("courseId")
        if file_course_id == course_id:
            result.append(file)
    return result

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
            file_course_id = file.get("course_id") or file.get("courseId")
            if file["id"] == file_id and file_course_id == course_id:
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
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
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            
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
    
    def call_gemini_multimodal_api(self, file_path, file_type, prompt):
        """调用Gemini多模态API处理图片、音频或视频文件"""
        try:
            # 获取API密钥
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            
            if not api_key:
                return "错误: 未设置Google AI API密钥。请在.env文件中配置GOOGLE_AI_API_KEY。"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            
            # 根据文件类型设置不同的大小限制
            if file_type == 'video':
                max_size = 100 * 1024 * 1024  # 视频文件限制100MB
            elif file_type == 'audio':
                max_size = 20 * 1024 * 1024   # 音频文件限制20MB
            else:
                max_size = 10 * 1024 * 1024   # PDF等其他文件限制10MB
            
            if file_size > max_size:
                size_mb = file_size/1024/1024
                limit_mb = max_size/1024/1024
                return f"文件大小({size_mb:.2f}MB)超过限制({limit_mb:.0f}MB)。请上传更小的文件。"
            
            # 读取文件数据
            with open(file_path, 'rb') as file:
                file_bytes = file.read()
            
            # 确定MIME类型
            mime_type = ""
            if file_type == "audio":
                if file_path.endswith('.mp3'):
                    mime_type = "audio/mpeg"
                elif file_path.endswith('.wav'):
                    mime_type = "audio/wav"
                elif file_path.endswith('.m4a'):
                    mime_type = "audio/mp4"
                else:
                    mime_type = "audio/mpeg"  # 默认
            elif file_type == "video":
                if file_path.endswith('.mp4'):
                    mime_type = "video/mp4"
                elif file_path.endswith('.avi'):
                    mime_type = "video/x-msvideo"
                elif file_path.endswith('.mov'):
                    mime_type = "video/quicktime"
                else:
                    mime_type = "video/mp4"  # 默认
            elif file_type == "image":
                if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    mime_type = "image/jpeg"
                elif file_path.endswith('.png'):
                    mime_type = "image/png"
                elif file_path.endswith('.gif'):
                    mime_type = "image/gif"
                elif file_path.endswith('.webp'):
                    mime_type = "image/webp"
                else:
                    mime_type = "image/jpeg"  # 默认
            elif file_type == "pdf":
                mime_type = "application/pdf"
            
            # 使用最新的gemini-2.0-flash模型
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            # 将文件编码为Base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # 构建请求体
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"请用中文回答：{prompt}"
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": file_base64
                                }
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
                
                return "AI未能生成有效回复。这可能是因为文件过大或格式不受支持。"
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_details = error_json["error"]["message"]
                except:
                    pass
                
                return f"API调用失败: HTTP {response.status_code}\n{error_details}\n\n这可能是因为文件太大或格式不受支持。"
        
        except Exception as e:
            return f"处理{file_type}文件时出错: {str(e)}"
    
    def process_pdf(self, file_path):
        """处理PDF文件并提取文本内容"""
        try:
            # 直接调用多模态API处理PDF文件
            return self.call_gemini_multimodal_api(file_path, "pdf", "请分析这个PDF文件并提供详细信息和内容摘要。如果内容中包含问题，请回答这些问题。")
        except Exception as e:
            # 如果多模态API处理失败，回退到传统提取方法
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    total_pages = len(pdf_reader.pages)
                    
                    # 添加PDF的基本信息
                    text += f"PDF文件包含 {total_pages} 页\n\n"
                    
                    # 提取文本内容
                    for i, page in enumerate(pdf_reader.pages):
                        page_content = page.extract_text() or "【此页无文本内容】"
                        text += f"--- 第 {i+1} 页 ---\n{page_content}\n\n"
                    
                    # 处理提取的文本
                    prompt = f"""
                    我上传了一个PDF文件，其内容如下:
                    
                    {text}
                    
                    请根据文件内容进行分析并给出专业的回复。如果内容中包含问题，请回答这些问题。
                    如果是一般内容，请总结主要观点并提出建议。
                    """
                    
                    return self.call_google_ai_api(prompt)
            except Exception as e2:
                raise Exception(f"PDF处理错误: {str(e)}, 备用处理也失败: {str(e2)}")
    
    def do_POST(self):
        # 文件上传功能
