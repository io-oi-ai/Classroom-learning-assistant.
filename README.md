# AI学习助手

这是一个基于Google Gemini API的AI学习助手，可以处理文本对话和多种文件类型（包括PDF、音频和视频）。系统使用最新的Gemini 2.0 Flash模型，支持多模态交互。

## 功能特点

- **文本对话**：与AI进行自然语言对话，提问各类问题
- **PDF文件处理**：上传PDF文档，AI会分析内容并提供摘要和见解
- **音频处理**：上传音频文件，AI会进行语音识别和内容分析
- **视频处理**：上传视频文件，AI会分析视频内容、场景和提供转录

## 技术架构

- **前端**：原生HTML、CSS和JavaScript
- **后端**：Python HTTP服务器
- **AI模型**：Google Gemini 2.0 Flash (支持多模态输入)

## 使用方法

### 系统要求
- Python 3.7+
- 浏览器：Chrome、Firefox、Safari或Edge
- 有效的Google AI API密钥

### 安装步骤

1. 克隆本仓库
```bash
git clone <仓库地址>
cd 大学生课堂
```

2. 安装依赖
```bash
pip install requests PyPDF2
```

3. 配置API密钥
在终端中设置环境变量或创建.env文件:
```bash
export GOOGLE_AI_API_KEY=你的API密钥
```

4. 启动后端服务
```bash
cd backend
python run.py
```

5. 启动前端
```bash
cd frontend
python -m http.server 3000
```

6. 打开浏览器访问
```
http://localhost:3000
```

## 使用限制

- PDF文件：支持大部分标准PDF格式
- 音频文件：支持mp3、wav、m4a格式，大小限制20MB
- 视频文件：支持mp4、avi、mov格式，大小限制20MB，时长最长90分钟

## 分支说明

- **main**: 主分支，稳定版本
- **gemini-2.0-flash**: 使用Gemini 2.0 Flash模型的版本
- **enhanced-file-handling**: 增强文件处理功能的版本（当前分支）

## 系统架构

### 前端
- 轻量级网页界面，提供文字对话和文件上传两种主要交互方式
- 异步通信，实时展示AI回复

### 后端
- Python简易HTTP服务器
- 文件处理模块：支持PDF、音频和视频
- Google Gemini API集成模块

## 未来计划
- 添加聊天历史保存功能
- 增加更多文件格式支持
- 优化用户界面，添加更多交互元素
- 增加响应式设计，支持移动设备

## 故障排除

如遇问题，请检查：
1. API密钥是否有效
2. 网络连接是否稳定
3. 文件大小是否超出限制
4. 文件格式是否受支持

## 贡献指南

欢迎提交Pull Request或Issues来帮助改进这个项目。

## 许可证

MIT License 