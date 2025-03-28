# AI智能助手系统

这是一个基于Google AI Studio API的智能助手系统，支持多模态输入（PDF、音频、视频）并能够进行智能回复。

## 功能特点

1. 多模态输入支持
   - PDF文档上传和解析
   - 音频文件上传和转写
   - 视频文件上传和内容提取

2. AI智能回复
   - 基于上传内容进行智能分析和回复
   - 支持上下文理解
   - 多语言支持

## 技术架构

- 后端：Python FastAPI
- 前端：React + TypeScript
- 文件处理：
  - PDF处理：PyPDF2
  - 音频处理：SpeechRecognition
  - 视频处理：MoviePy
- AI接口：Google AI Studio API

## 环境要求

- Python 3.8+
- Node.js 14+
- Google AI Studio API密钥

## 安装步骤

1. 克隆项目
```bash
git clone [项目地址]
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 配置环境变量
创建 `.env` 文件并添加以下配置：
```
GOOGLE_AI_API_KEY=你的API密钥
```

## 使用方法

1. 启动后端服务
```bash
cd backend
uvicorn main:app --reload
```

2. 启动前端服务
```bash
cd frontend
npm start
```

3. 访问系统
打开浏览器访问 http://localhost:3000

## API文档

### 文件上传接口

1. PDF上传
```
POST /api/upload/pdf
Content-Type: multipart/form-data
```

2. 音频上传
```
POST /api/upload/audio
Content-Type: multipart/form-data
```

3. 视频上传
```
POST /api/upload/video
Content-Type: multipart/form-data
```

### AI对话接口

```
POST /api/chat
Content-Type: application/json
```

## 注意事项

1. 请确保上传的文件大小不超过系统限制
2. 支持的音频格式：WAV, MP3, M4A
3. 支持的视频格式：MP4, AVI, MOV
4. 请妥善保管API密钥，不要泄露给他人

## 更新日志

### v1.0.0 (2024-03-21)
- 初始版本发布
- 支持基础的文件上传功能
- 集成Google AI Studio API 