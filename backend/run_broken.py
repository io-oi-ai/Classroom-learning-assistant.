#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import uuid
import base64
import cgi
import requests
import PyPDF2
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PIL import Image, ImageDraw, ImageFont
import textwrap
import fitz  # PyMuPDF for PDF to image conversion
import cv2  # OpenCV for video processing
import numpy as np
from io import BytesIO

# 定义上传和数据目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 确保目录存在
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 数据文件路径
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
FILES_FILE = os.path.join(DATA_DIR, 'files.json')
NOTE_CARDS_FILE = os.path.join(DATA_DIR, 'note_cards.json')

# 初始化数据文件
def init_data_files():
    if not os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"courses": []}, f, ensure_ascii=False)
    
    if not os.path.exists(FILES_FILE):
        with open(FILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"files": []}, f, ensure_ascii=False)
            
    if not os.path.exists(NOTE_CARDS_FILE):
        with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"cards": []}, f, ensure_ascii=False)

# 数据操作函数
def get_courses():
    with open(COURSES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_courses(data):
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_files():
    with open(FILES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_files(data):
    with open(FILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_note_cards(course_id=None):
    """获取笔记卡片，可按课程筛选"""
    with open(NOTE_CARDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if course_id:
            return [card for card in data["cards"] if card["course_id"] == course_id]
        return data["cards"]

def save_note_cards(cards):
    """保存新的笔记卡片"""
    with open(NOTE_CARDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 添加新卡片
    for card in cards:
        data["cards"].append(card)
    
    with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def delete_note_card(card_id):
    """删除指定的笔记卡片"""
    try:
        with open(NOTE_CARDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 查找并删除卡片
        card_found = False
        for i, card in enumerate(data["cards"]):
            if card["id"] == card_id:
                # 删除关联的图片文件
                if card.get("image"):
                    image_path = os.path.join(UPLOAD_DIR, card["image"].lstrip('/uploads/'))
                    if os.path.exists(image_path):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            print(f"删除图片文件失败: {str(e)}")
                
                data["cards"].pop(i)
                card_found = True
                break
        
        if not card_found:
            return {"error": "卡片不存在"}
        
        # 保存更新后的数据
        with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": "卡片已删除"}
        
    except Exception as e:
        return {"error": f"删除卡片时出错: {str(e)}"}

def update_note_card(card_id, title, content):
    """更新指定的笔记卡片"""
    try:
        with open(NOTE_CARDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 查找并更新卡片
        card_found = False
        for card in data["cards"]:
            if card["id"] == card_id:
                card["title"] = title
                card["content"] = content
                card_found = True
                break
        
        if not card_found:
            return {"error": "卡片不存在"}
        
        # 保存更新后的数据
        with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": "卡片已更新"}
        
    except Exception as e:
        return {"error": f"更新卡片时出错: {str(e)}"}

def get_course(course_id):
    """根据ID获取单个课程信息"""
    courses_data = get_courses()
    for course in courses_data["courses"]:
        if course["id"] == course_id:
            return course
    return None

def create_course(name):
    courses_data = get_courses()
    course_id = str(uuid.uuid4())
    new_course = {
        "id": course_id,
        "name": name,
        "createTime": int(time.time())
    }
    courses_data["courses"].append(new_course)
    save_courses(courses_data)
    
    # 创建课程目录
    course_dir = os.path.join(UPLOAD_DIR, course_id)
    if not os.path.exists(course_dir):
        os.makedirs(course_dir)
        
    return new_course

def get_course_files(course_id):
    files_data = get_files()
    return [f for f in files_data["files"] if f["courseId"] == course_id]

def add_file_record(file_name, file_type, file_path, course_id, summary="", screenshots=None):
    files_data = get_files()
    file_id = str(uuid.uuid4())
    new_file = {
        "id": file_id,
        "name": file_name,
        "type": file_type,
        "path": file_path,
        "courseId": course_id,
        "uploadTime": int(time.time()),
        "summary": summary
    }
    
    # 如果有截图信息，添加到文件记录中
    if screenshots:
        new_file["screenshots"] = screenshots
    
    files_data["files"].append(new_file)
    save_files(files_data)
    return new_file

# 删除文件
def delete_file(file_id, course_id):
    """删除文件记录和物理文件"""
    try:
        # 获取文件记录
        files_data = get_files()
        file_found = False
        file_to_delete = None
        
        # 查找要删除的文件
        for i, file in enumerate(files_data["files"]):
            if file["id"] == file_id:
                file_found = True
                file_to_delete = file
                files_data["files"].pop(i)
                break
        
        if not file_found:
            return {"error": "文件不存在"}
        
        # 检查文件是否属于指定课程
        if course_id and file_to_delete["courseId"] != course_id:
            return {"error": "无权删除该文件"}
        
        # 删除物理文件
        file_path = os.path.join(UPLOAD_DIR, file_to_delete["path"])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # 保存更新后的文件记录
        save_files(files_data)
        
        return {"success": True, "message": "文件已删除"}
        
    except Exception as e:
        return {"error": f"删除文件时出错: {str(e)}"}

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
            
        # 课程总结功能（全部文件）
        elif self.path.startswith('/api/courses/') and self.path.endswith('/summarize'):
            course_id = self.path.split('/')[3]
            response = self.do_GET_summarize_course(course_id)
            self.wfile.write(response.encode('utf-8'))
        
        # 特定文件总结功能
        elif self.path.startswith('/api/courses/') and '/summarize-files/' in self.path:
            # 解析 URL: /api/courses/{course_id}/summarize-files/{file_ids}
            parts = self.path.split('/')
            course_id = parts[3]
            file_ids = parts[5]  # 多个文件ID逗号分隔
            response = self.do_GET_summarize_files(course_id, file_ids)
            self.wfile.write(response.encode('utf-8'))
        
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
            
            # 使用最新的gemini-2.0-flash模型 (根据官方文档)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            # 将文件编码为Base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # 构建请求体，使用新的API格式
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
        
        # 生成笔记卡片
        elif self.path.startswith('/api/courses/') and '/generate-cards' in self.path:
            try:
                # 解析URL: /api/courses/{course_id}/generate-cards
                parts = self.path.split('/')
                course_id = parts[3]
                
                # 解析POST请求中的JSON数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                file_ids = data.get('file_ids', [])
                
                response = self.do_POST_generate_cards(course_id, file_ids)
                self.wfile.write(response.encode('utf-8'))
            
            except Exception as e:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": f"生成笔记卡片失败: {str(e)}"
                }).encode('utf-8'))
        
        # 聊天功能
        elif self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                course_id = data.get('courseId')
                is_new_chat = data.get('isNewChat', False)  # 新增参数，判断是否是新的对话
                selected_files = data.get('selectedFiles', [])  # 新增参数，选择的文件ID列表
                
                if not message.strip():
                    self.wfile.write(json.dumps({
                        "error": "消息不能为空"
                    }).encode('utf-8'))
                    return
                
                # 构建上下文
                context = ""
                
                # 如果有选择的文件，优先使用选择的文件
                if selected_files and course_id:
                    course_files = get_course_files(course_id)
                    selected_file_objects = [f for f in course_files if f['id'] in selected_files]
                    
                    if selected_file_objects:
                        context = "基于以下选择的课程材料回答问题：\n\n"
                        for file in selected_file_objects:
                            context += f"文件：{file['name']} (类型: {file['type']})\n"
                            context += f"内容摘要：{file.get('summary', '无摘要')}\n\n"
                        context += f"\n用户问题：{message}\n\n请基于上述材料内容回答问题，如果问题与材料内容不相关，请说明并提供一般性回答。"
                        message = context
                
                # 如果没有选择文件，但指定了课程ID且不是新对话，使用所有课程文件
                elif course_id and not is_new_chat and not selected_files:
                    course_files = get_course_files(course_id)
                    if course_files:
                        context = "基于以下课程材料回答问题：\n\n"
                        for file in course_files:
                            context += f"文件：{file['name']}\n摘要：{file.get('summary', '无摘要')}\n\n"
                        message = context + "\n用户问题：" + message
                
                # 调用AI接口
                ai_response = self.call_google_ai_api(message)
                
                self.wfile.write(json.dumps({
                    "response": ai_response
                }).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": str(e)
                }).encode('utf-8'))
        
        # 文件上传功能
        elif self.path == '/api/upload':
            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # 检查是否有文件上传
                if 'file' not in form:
                    self.wfile.write(json.dumps({
                        "error": "没有找到上传的文件"
                    }).encode('utf-8'))
                    return
                
                # 检查是否提供了课程ID
                if 'courseId' not in form:
                    self.wfile.write(json.dumps({
                        "error": "未指定课程ID"
                    }).encode('utf-8'))
                    return
                
                # 获取上传的文件和课程ID
                file_item = form['file']
                course_id = form['courseId'].value
                
                # 根据文件扩展名确定文件类型
                filename = file_item.filename
                file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
                
                if file_extension == 'pdf':
                    file_type = 'pdf'
                elif file_extension in ['mp3', 'wav', 'ogg', 'm4a']:
                    file_type = 'audio'
                elif file_extension in ['mp4', 'avi', 'mov', 'webm']:
                    file_type = 'video'
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    file_type = 'image'
                else:
                    file_type = 'document'
                
                # 检查文件大小
                file_content = file_item.file.read()
                file_size = len(file_content)
                
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
                    self.wfile.write(json.dumps({
                        "error": f"文件大小({size_mb:.2f}MB)超过限制({limit_mb:.0f}MB)。请上传更小的文件。"
                    }).encode('utf-8'))
                    return
                
                # 检查课程是否存在
                courses_data = get_courses()
                course_exists = any(course["id"] == course_id for course in courses_data["courses"])
                if not course_exists:
                    self.wfile.write(json.dumps({
                        "error": f"课程ID不存在: {course_id}"
                    }).encode('utf-8'))
                    return
                
                # 检查文件类型是否支持
                if file_type not in ['pdf', 'audio', 'video', 'image', 'document']:
                    self.wfile.write(json.dumps({
                        "error": f"不支持的文件类型: {file_type}"
                    }).encode('utf-8'))
                    return
                
                # 创建课程文件目录
                course_dir = os.path.join(UPLOAD_DIR, course_id)
                if not os.path.exists(course_dir):
                    os.makedirs(course_dir)
                
                # 创建临时文件
                temp_file_path = os.path.join(course_dir, f"{int(time.time())}_{file_item.filename}")
                
                # 保存上传的文件
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content)
                
                try:
                    # 提取媒体内容（截图等）
                    extracted_media = self.extract_media_content(temp_file_path, file_type, course_id)
                    
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                        # 如果提取了PDF截图，添加到响应中
                        if extracted_media["screenshots"]:
                            ai_response += f"\n\n📸 {extracted_media['description']}"
                    elif file_type == 'audio':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
                        # 如果提取了视频关键帧，添加到响应中
                        if extracted_media["screenshots"]:
                            ai_response += f"\n\n🎬 {extracted_media['description']}"
                    elif file_type == 'image':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "image", "请分析这张图片并提供详细描述、内容分析和总结")
                    elif file_type == 'document':
                        # 对于其他文档类型，尝试作为文本处理
                        ai_response = f"已上传文档文件：{filename}。文件类型：{file_type}。请在聊天中询问相关问题以获取更多信息。"
                    else:
                        raise Exception("不支持的文件类型")
                    
                    # 记录文件信息
                    summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    new_file = add_file_record(
                        file_name=file_item.filename,
                        file_type=file_type,
                        file_path=os.path.relpath(temp_file_path, UPLOAD_DIR),
                        course_id=course_id,
                        summary=summary,
                        screenshots=extracted_media["screenshots"] if extracted_media["screenshots"] else None
                    )
                    
                    self.wfile.write(json.dumps({
                        "success": True,
                        "file": new_file,
                        "content": ai_response,
                        "extracted_media": extracted_media
                    }).encode('utf-8'))
                    
                except Exception as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    raise e
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"处理文件时出错: {str(e)}"
                }).encode('utf-8'))
        
        # 编辑笔记卡片
        elif self.path.startswith('/api/cards/') and self.path.endswith('/edit'):
            # 解析URL: /api/cards/{card_id}/edit
            parts = self.path.split('/')
            if len(parts) >= 4:
                card_id = parts[3]
            
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                    title = data.get('title', '').strip()
                    content = data.get('content', '').strip()
                    
                    if not title or not content:
                        self.wfile.write(json.dumps({
                            "error": "标题和内容不能为空"
                        }).encode('utf-8'))
                        return
                
                    result = update_note_card(card_id, title, content)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "error": f"编辑卡片失败: {str(e)}"
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "error": "无效的编辑请求路径"
                }).encode('utf-8'))

        else:
            self.wfile.write(json.dumps({
                "error": "路径不存在"
            }).encode('utf-8'))

    def do_GET_summarize_course(self, course_id):
        try:
            course_files = get_course_files(course_id)
            if not course_files:
                return json.dumps({
                    "error": "该课程没有文件"
                }, ensure_ascii=False)
            
            course = get_course(course_id)
            if not course:
                return json.dumps({
                    "error": "课程不存在"
                }, ensure_ascii=False)
            
            # 构建高价值内容提取的提示词
            prompt = f"""请根据以下课程《{course['name']}》的所有学习材料进行智能分析，提取和分级重点内容。
            
在分析时，请特别关注以下几个方面：
1. 教师在讲解时重复次数多的内容（这通常是重点知识点）
2. 教师在讲解时声音明显提高的部分（这常常是需要特别注意的内容）
3. 包含"考点"、"重点"、"关键"、"记住"、"一定要"等关键词的内容
4. 教师在讲解时花费较长时间停留讲解的概念或知识点

请将重点内容分成三个等级：
- 【核心重点】：满足多个维度的重要内容，或者被教师特别强调的内容，考试必考点
- 【次要重点】：具有一定重要性但不是最核心的内容，理解课程必要的知识点
- 【一般知识点】：背景知识或基础概念，对理解整体内容有帮助的知识点

请将分析结果组织为以下几个部分：
1. 课程核心内容：简要概括课程的主要内容（150字以内）
2. 重点内容分级：
   - 核心重点（用★★★标记）
   - 次要重点（用★★标记）
   - 一般知识点（用★标记）
3. 学习建议：基于重点分析给出学习策略和方法（150字以内）

以下是课程的所有学习材料内容：
"""
            
            # 添加文件内容到提示词
            for file in course_files:
                prompt += f"\n文件：{file['name']} (类型: {file['type']})\n"
                prompt += f"内容：{file.get('summary', '无摘要')}\n\n"
            
            # 调用AI接口获取总结
            try:
                summary = self.call_google_ai_api(prompt)
                if not summary:
                    return json.dumps({
                        "error": "AI分析返回了空结果，请重试"
                    }, ensure_ascii=False)
                
                return json.dumps({
                    "summary": summary
                }, ensure_ascii=False)
            except Exception as e:
                print(f"调用AI API时出错: {str(e)}")
                return json.dumps({
                    "error": f"提取重点失败: {str(e)}"
                }, ensure_ascii=False)
                
        except Exception as e:
            print(f"总结课程时出错: {str(e)}")
            return json.dumps({
                "error": f"提取重点失败: {str(e)}"
            }, ensure_ascii=False)

    # 处理DELETE请求
    def do_DELETE(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 删除文件 - 修复路径处理
        if self.path.startswith('/api/courses/') and '/files/' in self.path:
            # 解析URL: /api/courses/{course_id}/files/{file_id}
            parts = self.path.split('/')
            if len(parts) >= 6:
                course_id = parts[3]
                file_id = parts[5]
                
                try:
                    result = delete_file(file_id, course_id)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                    
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "error": "无效的删除请求路径"
                }).encode('utf-8'))
        
        # 删除笔记卡片
        elif self.path.startswith('/api/cards/'):
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

    def do_GET_summarize_files(self, course_id, file_ids):
        try:
            # 检查课程是否存在
            course = get_course(course_id)
            if not course:
                return json.dumps({
                    "error": "课程不存在"
                }, ensure_ascii=False)
            
            # 获取所有课程文件
            all_course_files = get_course_files(course_id)
            
            # 筛选出指定的文件
            file_id_list = file_ids.split(',')
            selected_files = [file for file in all_course_files if file["id"] in file_id_list]
            
            if not selected_files:
                return json.dumps({
                    "error": "未找到指定的文件"
                }, ensure_ascii=False)
            
            # 构建高价值内容提取的提示词
            prompt = f"""请根据以下《{course['name']}》课程的选定学习材料进行智能分析，提取和分级重点内容。
            
在分析时，请特别关注以下几个方面：
1. 教师在讲解时重复次数多的内容（这通常是重点知识点）
2. 教师在讲解时声音明显提高的部分（这常常是需要特别注意的内容）
3. 包含"考点"、"重点"、"关键"、"记住"、"一定要"等关键词的内容
4. 教师在讲解时花费较长时间停留讲解的概念或知识点

请将重点内容分成三个等级：
- 【核心重点】：满足多个维度的重要内容，或者被教师特别强调的内容，考试必考点
- 【次要重点】：具有一定重要性但不是最核心的内容，理解课程必要的知识点
- 【一般知识点】：背景知识或基础概念，对理解整体内容有帮助的知识点

请将分析结果组织为以下几个部分：
1. 材料核心内容：简要概括主要内容（150字以内）
2. 重点内容分级：
   - 核心重点（用★★★标记）
   - 次要重点（用★★标记）
   - 一般知识点（用★标记）
3. 学习建议：基于重点分析给出学习策略和方法（150字以内）

以下是所选的学习材料内容：
"""
            
            # 添加文件内容到提示词
            for file in selected_files:
                prompt += f"\n文件：{file['name']} (类型: {file['type']})\n"
                prompt += f"内容：{file.get('summary', '无摘要')}\n\n"
            
            # 调用AI接口获取总结
            try:
                summary = self.call_google_ai_api(prompt)
                if not summary:
                    return json.dumps({
                        "error": "AI分析返回了空结果，请重试"
                    }, ensure_ascii=False)
                
                return json.dumps({
                    "summary": summary
                }, ensure_ascii=False)
            except Exception as e:
                print(f"调用AI API时出错: {str(e)}")
                return json.dumps({
                    "error": f"提取重点失败: {str(e)}"
                }, ensure_ascii=False)
                
        except Exception as e:
            print(f"总结选定文件时出错: {str(e)}")
            return json.dumps({
                "error": f"提取重点失败: {str(e)}"
            }, ensure_ascii=False)

    def should_generate_image(self, content):
        """智能判断是否需要为内容生成图片"""
        # 判断是否包含可视化价值的关键词
        visual_keywords = [
            "流程", "过程", "步骤", "阶段", "结构", 
            "关系", "分类", "类型", "对比", "比较",
            "图", "表格", "公式", "模型", "原理",
            "机制", "系统", "框架", "架构"
            ]
            
        # 检查内容中是否包含这些关键词
        has_visual_value = any(keyword in content for keyword in visual_keywords)
            
        # 检查内容长度，太短的内容可能不值得生成图片
        suitable_length = len(content) > 50
        
        return has_visual_value and suitable_length
    
    def generate_knowledge_image(self, content, course_id):
        """使用Gemini生成知识点配图"""
        try:
            # 构建提示词
            prompt = f"""
            请为以下教育知识点创建一张黑板风格的手绘教育插图:
            
            {content}
            
            该图应该:
            1. 使用黑板绿色背景和白色/彩色粉笔风格
            2. 包含简洁清晰的视觉元素来解释概念
            3. 使用箭头、图表或图示来表示关系
            4. 添加简短关键词标注，但保持整体简洁
            5. 适合教育场景，帮助学生理解概念
            """
            
            # 调用Gemini图像生成API
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key={api_key}"
            
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
                "generation_config": {
                    "temperature": 0.4
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                # 提取图片URL
                for candidate in result.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            # 保存Base64图像到文件
                            image_data = part["inlineData"]["data"]
                            image_path = self.save_base64_image(image_data, course_id)
                            return image_path
                            
                # 如果API没有返回图像，使用备选方案
                return self.generate_fallback_image(content, course_id)
            else:
                print(f"图像生成API错误: {response.status_code}")
                return self.generate_fallback_image(content, course_id)
                
        except Exception as e:
            print(f"生成图像时出错: {str(e)}")
            return self.generate_fallback_image(content, course_id)
    
    def save_base64_image(self, base64_data, course_id):
        """保存Base64格式的图像到文件"""
        try:
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            # 保存图像
            image_filename = f"note_image_{int(time.time())}.png"
            image_path = os.path.join(course_img_dir, image_filename)
                                
            # 解码Base64并保存
            image_data = base64.b64decode(base64_data)
            with open(image_path, 'wb') as f:
                f.write(image_data)
                                
                                # 返回相对URL路径
            return f"/uploads/{course_id}/images/{image_filename}"
        except Exception as e:
            print(f"保存图像时出错: {str(e)}")
            return None
    
    def generate_fallback_image(self, content, course_id):
        """备选图像生成方案"""
        try:
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            # 创建一个带有绿色背景的图像(模拟黑板)
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color=(40, 70, 40))
            draw = ImageDraw.Draw(image)
            
            # 使用可用字体
            try:
                font = ImageFont.truetype("Arial.ttf", 28)
            except:
                font = ImageFont.load_default()
            
            # 文字换行处理
            margin = 50
            content_preview = content[:500] + "..." if len(content) > 500 else content
            lines = textwrap.wrap(content_preview, width=40)
            y_position = margin
            
            # 绘制文本
            for line in lines:
                draw.text((margin, y_position), line, font=font, fill=(255, 255, 255))
                y_position += 40
                if y_position > height - margin:
                    break
                    
            # 添加边框
            draw.rectangle([(10, 10), (width-10, height-10)], outline=(200, 200, 200), width=2)
            
            # 保存图像
            image_filename = f"fallback_{int(time.time())}.png"
            image_path = os.path.join(course_img_dir, image_filename)
            image.save(image_path)
            # 返回相对URL路径
            return f"/uploads/{course_id}/images/{image_filename}"
        
        except Exception as e:
            print(f"备选图像生成失败: {str(e)}")
            # 如果完全失败，返回None
            return None

    def extract_pdf_screenshots(self, pdf_path, course_id, max_pages=5):
        """从PDF中提取关键页面截图"""
        try:
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            screenshots = []
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # 智能选择页面：均匀分布 + 首页
            if total_pages <= max_pages:
                page_indices = list(range(total_pages))
            else:
                # 总是包含第一页
                page_indices = [0]
                # 从剩余页面中均匀选择
                remaining_slots = max_pages - 1
                if remaining_slots > 0:
                    step = (total_pages - 1) // remaining_slots
                    for i in range(1, remaining_slots + 1):
                        page_idx = min(i * step, total_pages - 1)
                        if page_idx not in page_indices:
                            page_indices.append(page_idx)
            
            for page_num in page_indices:
                try:
                    page = doc[page_num]
                    # 转换为图片 (300 DPI for good quality)
                    mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
                    pix = page.get_pixmap(matrix=mat)
                    
                    # 转换为PIL Image
                    img_data = pix.tobytes("png")
                    img = Image.open(BytesIO(img_data))
            
                    # 保存截图
                    screenshot_filename = f"pdf_page_{page_num + 1}_{int(time.time())}.png"
                    screenshot_path = os.path.join(course_img_dir, screenshot_filename)
                    img.save(screenshot_path, "PNG")
                    
                    # 返回相对URL路径
                    screenshot_url = f"/uploads/{course_id}/images/{screenshot_filename}"
                    screenshots.append({
                        "url": screenshot_url,
                        "page": page_num + 1,
                        "description": f"PDF第{page_num + 1}页"
                    })
                    
                except Exception as e:
                    print(f"提取PDF第{page_num + 1}页失败: {str(e)}")
                    continue
            
            doc.close()
            return screenshots
            
        except Exception as e:
            print(f"PDF截图提取失败: {str(e)}")
            return []

    def extract_video_keyframes(self, video_path, course_id, max_frames=8):
        """从视频中提取关键帧"""
        try:
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            keyframes = []
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                print(f"无法打开视频文件: {video_path}")
                return []
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # 计算关键帧位置（均匀分布）
            if total_frames <= max_frames:
                frame_indices = list(range(0, total_frames, max(1, total_frames // max_frames)))
            else:
                step = total_frames // max_frames
                frame_indices = [i * step for i in range(max_frames)]
            
            for i, frame_idx in enumerate(frame_indices):
                try:
                    # 跳转到指定帧
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    
                    if not ret:
                        continue
                    
                    # 转换BGR到RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    
                    # 计算时间戳
                    timestamp = frame_idx / fps if fps > 0 else 0
                    minutes = int(timestamp // 60)
                    seconds = int(timestamp % 60)
            
                    # 保存关键帧
                    keyframe_filename = f"video_frame_{minutes:02d}m{seconds:02d}s_{int(time.time())}.png"
                    keyframe_path = os.path.join(course_img_dir, keyframe_filename)
                    img.save(keyframe_path, "PNG")
                    
                    # 返回相对URL路径
                    keyframe_url = f"/uploads/{course_id}/images/{keyframe_filename}"
                    keyframes.append({
                        "url": keyframe_url,
                        "timestamp": f"{minutes:02d}:{seconds:02d}",
                        "description": f"视频截图 {minutes:02d}:{seconds:02d}"
                    })
                    
                except Exception as e:
                    print(f"提取视频第{i}帧失败: {str(e)}")
                    continue
            
            cap.release()
            return keyframes
            
        except Exception as e:
            print(f"视频关键帧提取失败: {str(e)}")
            return []

    def extract_media_content(self, file_path, file_type, course_id):
        """从媒体文件中提取内容（截图等）"""
        extracted_content = {
            "screenshots": [],
            "description": ""
        }
        
        try:
            if file_type == "pdf":
                # 提取PDF截图
                screenshots = self.extract_pdf_screenshots(file_path, course_id)
                extracted_content["screenshots"] = screenshots
                extracted_content["description"] = f"从PDF中提取了{len(screenshots)}张页面截图"
                
            elif file_type == "video":
                # 提取视频关键帧
                keyframes = self.extract_video_keyframes(file_path, course_id)
                extracted_content["screenshots"] = keyframes
                extracted_content["description"] = f"从视频中提取了{len(keyframes)}个关键帧"
                
            return extracted_content
            
        except Exception as e:
            print(f"媒体内容提取失败: {str(e)}")
            return extracted_content

    def extract_knowledge_points(self, course, files):
        """从课程内容中提取关键知识点"""
        try:
            # 获取课程信息
            course_name = course.get("name", "未命名课程")
            
            # 构建更详细的提示词
            prompt = f"""请从以下《{course_name}》课程材料中深度分析并提取6-10个核心知识点，格式为JSON数组。

分析要求：
1. 深入理解课程内容的核心概念和重要知识点
2. 每个知识点应该是独立的、完整的学习单元
3. 优先提取具有教学价值和实用性的内容
4. 包含定义、原理、应用、例子等多个维度

每个知识点应包含以下属性:
1. "title": 知识点标题（8-15字，准确概括核心概念）
2. "content": 知识点的详细内容描述（200-500字），应包含：
   - 核心定义或概念解释
   - 重要原理或机制说明
   - 实际应用场景或例子
   - 与其他知识点的关联
   - 学习要点或注意事项

内容质量要求:
- 每个知识点内容丰富，具有教育价值
- 语言清晰易懂，适合学习理解
- 包含具体的例子或应用场景
- 避免过于抽象，要有实际意义
- 适合生成教育插图或图表

提取的知识点JSON数组格式:
[
  {{
    "title": "具体知识点标题",
    "content": "详细的知识点内容描述，包含定义、原理、应用、例子等..."
  }},
  {{
    "title": "另一个知识点标题",
    "content": "另一个知识点的详细描述..."
  }}
]

以下是课程材料的完整内容:
"""
            
            # 添加文件内容到提示词，包含更多详细信息
            for file in files:
                prompt += f"\n=== 文件: {file['name']} (类型: {file['type']}) ===\n"
                
                # 获取完整的文件内容摘要
                full_summary = file.get('summary', '无摘要')
                if len(full_summary) > 50:  # 如果摘要较长，使用完整内容
                    prompt += f"详细内容: {full_summary}\n"
            else:
                    prompt += f"内容摘要: {full_summary}\n"
                
                # 如果有截图信息，也包含进来
                if 'screenshots' in file and file['screenshots']:
                    prompt += f"包含 {len(file['screenshots'])} 张截图/图表\n"
                
                prompt += "\n"
            
            prompt += "\n请基于以上所有材料，提取最有价值的核心知识点，确保每个知识点内容详实、教育价值高。"
            
            # 调用AI接口提取知识点
            response = self.call_google_ai_api(prompt)
            
            # 解析JSON
            try:
                # 查找并提取JSON部分
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    knowledge_points = json.loads(json_str)
                    
                    # 验证知识点质量
                    valid_points = []
                    for point in knowledge_points:
                        if (point.get('title') and point.get('content') and 
                            len(point['content']) >= 100):  # 确保内容足够详细
                            valid_points.append(point)
                    
                    return valid_points
                else:
                    # 尝试直接解析，可能整个响应就是JSON
                    knowledge_points = json.loads(response)
                    return knowledge_points
            except Exception as e:
                print(f"解析知识点JSON时出错: {str(e)}")
                print(f"AI响应内容: {response[:500]}...")
                # 如果解析失败，返回空列表
                return []
                
        except Exception as e:
            print(f"提取知识点时出错: {str(e)}")
            return []
    
    def do_POST_generate_cards(self, course_id=None, file_ids=None):
        """生成笔记卡片"""
        try:
            # 获取课程
            course = get_course(course_id)
            if not course:
                return json.dumps({
                    "success": False,
                    "error": "课程不存在"
                })
            
            # 获取文件
            if file_ids and isinstance(file_ids, list):
                files = [file for file in get_course_files(course_id) if file["id"] in file_ids]
            else:
                files = get_course_files(course_id)
            
            if not files:
                return json.dumps({
                    "success": False,
                    "error": "没有可用的文件"
                })
            
            # 提取关键知识点
            knowledge_points = self.extract_knowledge_points(course, files)
            
            if not knowledge_points:
                return json.dumps({
                    "success": False,
                    "error": "无法从课程内容中提取知识点"
                })
            
            # 收集所有可用的截图
            available_screenshots = []
            for file in files:
                if "screenshots" in file and file["screenshots"]:
                    available_screenshots.extend(file["screenshots"])
            
            # 为每个知识点生成配图
            cards = []
            screenshot_index = 0
            
            for point in knowledge_points:
                title = point.get("title", "未命名知识点")
                content = point.get("content", "")
            
                # 优先使用提取的截图，然后考虑AI生成
                image_url = None
                
                # 1. 优先使用提取的截图
                if available_screenshots and screenshot_index < len(available_screenshots):
                    screenshot = available_screenshots[screenshot_index]
                    image_url = screenshot["url"]
                    screenshot_index += 1
                
                # 2. 如果没有可用截图，且内容适合生成图片，则AI生成
                elif self.should_generate_image(content):
                    image_url = self.generate_knowledge_image(content, course_id)
                
                # 创建卡片
                card = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "content": content,
                    "image": image_url,
                    "course_id": course_id,
                    "file_ids": file_ids if file_ids else [file["id"] for file in files],
                    "created_at": int(time.time()),
                    "image_source": "extracted" if image_url and screenshot_index > 0 else "generated" if image_url else "none"
                }
                cards.append(card)
            
            # 保存到数据库
            save_note_cards(cards)
            
            return json.dumps({
                "success": True,
                "cards": cards
            })
        except Exception as e:
            print(f"生成笔记卡片时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return json.dumps({
                "success": False,
                "error": str(e)
            })

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'启动服务器在端口 {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    # 初始化数据文件
    init_data_files()
    run() 