import os
import json
import tempfile
import shutil
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
from urllib.parse import parse_qs
import PyPDF2
import time
import base64

# 创建上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/':
            response = {"message": "欢迎使用AI智能助手"}
            self.wfile.write(json.dumps(response).encode())
        else:
            response = {"error": "路径不存在"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                
                if not message.strip():
                    response = {"error": "消息不能为空"}
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # 调用Google AI API
                ai_response = self.call_google_ai_api(message)
                
                response = {
                    "response": ai_response
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                response = {"error": str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        elif self.path.startswith('/api/upload/'):
            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # 检查是否有文件上传
                if 'file' not in form:
                    response = {"error": "没有找到上传的文件"}
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # 获取上传的文件
                file_item = form['file']
                file_type = self.path.split('/')[-1]  # 获取文件类型 (pdf, audio, video)
                
                # 检查文件类型是否支持
                if file_type not in ['pdf', 'audio', 'video']:
                    response = {"error": f"不支持的文件类型: {file_type}"}
                    self.wfile.write(json.dumps(response).encode())
                    return
                
                # 创建临时文件
                temp_file_path = os.path.join(UPLOAD_DIR, f"{int(time.time())}_{file_item.filename}")
                
                # 保存上传的文件
                with open(temp_file_path, 'wb') as f:
                    f.write(file_item.file.read())
                
                try:
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                    elif file_type == 'audio':
                        # 使用Gemini多模态API处理音频
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        # 使用Gemini多模态API处理视频
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
                    else:
                        raise Exception("不支持的文件类型")
                    
                    response = {
                        "content": ai_response
                    }
                    
                    self.wfile.write(json.dumps(response).encode())
                except Exception as e:
                    response = {"error": f"处理文件时出错: {str(e)}"}
                    self.wfile.write(json.dumps(response).encode())
                finally:
                    # 删除临时文件
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                
            except Exception as e:
                response = {"error": f"上传文件时出错: {str(e)}"}
                self.wfile.write(json.dumps(response).encode())
        else:
            response = {"error": "路径不存在"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
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
    
    def process_audio(self, file_path):
        """处理音频文件"""
        # 这里简化处理，实际中应调用语音识别API
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        return f"""
        您上传了一个音频文件，文件大小约为 {file_size_mb:.2f} MB。
        
        在真实应用中，我们会使用语音识别技术将此音频转换为文本。
        例如，我们可以使用Google Speech-to-Text API或其他语音识别服务。
        
        由于目前系统尚未集成实际的语音识别功能，我们无法提取音频内容，
        但您可以通过直接在对话框中输入问题来与AI智能助手交流。
        
        如有特定问题需要解答，请直接在聊天窗口中提问。
        """
    
    def process_video(self, file_path):
        """处理视频文件"""
        # 这里简化处理，实际中应提取视频的音频并调用语音识别API
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        return f"""
        您上传了一个视频文件，文件大小约为 {file_size_mb:.2f} MB。
        
        在真实应用中，我们会执行以下处理：
        1. 从视频中提取音频轨道
        2. 使用语音识别技术将音频转换为文本
        3. 对关键帧进行图像识别分析
        4. 综合分析视频内容并生成摘要
        
        由于目前系统尚未集成完整的视频处理功能，我们无法提取视频内容，
        但您可以通过直接在对话框中输入问题来与AI智能助手交流。
        
        如有特定问题需要解答，请直接在聊天窗口中提问。
        """
    
    def call_google_ai_api(self, prompt):
        """调用Google AI API处理文本"""
        try:
            # 获取API密钥
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            
            if not api_key:
                return "错误: 未设置Google AI API密钥。请在.env文件中配置GOOGLE_AI_API_KEY。"
            
            # 使用最新的gemini-2.0-flash模型 (根据官方文档)
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            }
            
            # 对提示词增加一些指导
            enhanced_prompt = f"""
            请用中文回答以下内容，保持专业性并提供完整、有深度的回答:
            
            {prompt}
            """
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": enhanced_prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                
                return "AI未能生成有效回复。请稍后再试或修改您的问题。"
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_details = error_json["error"]["message"]
                except:
                    pass
                
                return f"API调用失败: HTTP {response.status_code}\n{error_details}\n\n请检查您的API密钥是否有效，或稍后再试。"
        
        except requests.exceptions.ConnectionError:
            return "连接错误: 无法连接到Google AI服务。请检查您的网络连接。"
        except requests.exceptions.Timeout:
            return "超时错误: Google AI服务响应超时。请稍后再试。"
        except Exception as e:
            return f"API调用错误: {str(e)}\n\n请检查您的API密钥是否有效，或稍后再试。"
    
    def call_gemini_multimodal_api(self, file_path, file_type, prompt):
        """调用Gemini多模态API处理图片、音频或视频文件"""
        try:
            # 获取API密钥
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            
            if not api_key:
                return "错误: 未设置Google AI API密钥。请在.env文件中配置GOOGLE_AI_API_KEY。"
            
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

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"启动服务器在端口 {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run() 