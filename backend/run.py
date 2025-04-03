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

# 从环境变量获取端口
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')

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

# 初始化数据文件
def init_data_files():
    if not os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"courses": []}, f, ensure_ascii=False)
    
    if not os.path.exists(FILES_FILE):
        with open(FILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"files": []}, f, ensure_ascii=False)

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

def add_file_record(file_name, file_type, file_path, course_id, summary=""):
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

# 添加健康检查端点
def handle_health_check(handler):
    handler.send_response(200)
    handler.send_header('Content-type', 'application/json')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps({"status": "healthy"}).encode('utf-8'))

class SimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # 添加健康检查路由
        if self.path == '/api/health':
            return handle_health_check(self)
            
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
        
        # 聊天功能
        elif self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                course_id = data.get('courseId')
                is_new_chat = data.get('isNewChat', False)  # 新增参数，判断是否是新的对话
                
                if not message.strip():
                    self.wfile.write(json.dumps({
                        "error": "消息不能为空"
                    }).encode('utf-8'))
                    return
                
                # 如果指定了课程ID，且不是新对话，添加课程上下文
                if course_id and not is_new_chat:
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
        elif self.path.startswith('/api/upload/'):
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
                file_type = self.path.split('/')[-1]  # 获取文件类型 (pdf, audio, video)
                
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
                if file_type not in ['pdf', 'audio', 'video']:
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
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                    elif file_type == 'audio':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
                    else:
                        raise Exception("不支持的文件类型")
                    
                    # 记录文件信息
                    summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    add_file_record(
                        file_name=file_item.filename,
                        file_type=file_type,
                        file_path=temp_file_path,
                        course_id=course_id,
                        summary=summary
                    )
                    
                    self.wfile.write(json.dumps({
                        "content": ai_response
                    }).encode('utf-8'))
                    
                except Exception as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    raise e
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"处理文件时出错: {str(e)}"
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
        
        # 删除文件
        if self.path.startswith('/api/files/'):
            file_id = self.path.split('/')[3]
            
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                course_id = data.get('courseId')
                
                result = delete_file(file_id, course_id)
                
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": str(e)
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

def run():
    # 初始化数据文件
    init_data_files()
    
    # 启动服务器
    httpd = HTTPServer((HOST, PORT), SimpleHTTPRequestHandler)
    print(f"Server started at http://{HOST}:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    run() 