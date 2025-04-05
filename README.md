# 大学生课堂 - 智能学习助手

一款基于AI的智能学习助手系统，支持课程管理、文件上传分析、重点提取和智能问答功能。

## 主要功能

### 1. 课程管理
- 创建和管理多个课程
- 每个课程可包含多种学习材料

### 2. 文件上传与分析
- 支持上传PDF文档、音频(MP3/WAV/M4A)和视频(MP4/AVI/MOV)文件
- AI自动分析文件内容并生成摘要
- 简洁的文件管理界面，支持文件删除

### 3. 重点提取功能
- 基于多维度分析课程材料中的重点内容
  - 重复强调的内容
  - 语音强调的部分
  - 关键词标记("考点"、"重点"等)
  - 讲解停留时间长的概念
- 将重点内容分为三级：核心重点(★★★)、次要重点(★★)、一般知识点(★)
- 提供学习建议和策略

### 4. 智能问答
- 基于课程材料回答问题
- 支持新建对话，不带历史上下文
- 记录聊天历史

## 使用方法

1. **启动系统**
   - 后端服务器: `cd backend && python run.py`
   - 前端服务器: `cd frontend && python -m http.server 3000`
   - 访问地址: http://localhost:3000

2. **课程管理**
   - 点击"+ 新建课程"创建课程
   - 从左侧列表选择课程

3. **文件上传**
   - 选择一个课程后点击"上传文件"
   - 选择支持的文件类型(PDF/音频/视频)
   - 等待AI分析完成

4. **重点提取**
   - 选择课程后点击"重点提取"
   - 系统会分析课程中所有文件的内容
   - 以分级形式呈现重点内容

5. **智能问答**
   - 在右侧聊天区域输入问题
   - 点击右上角"+"按钮可以开始新对话

## 技术栈

- 后端: Python + HTTP Server
- 前端: HTML + CSS + JavaScript
- AI支持: Google Gemini API

## 注意事项

- 上传大文件可能会导致处理时间较长
- 部分特殊格式的文件可能无法正确解析
- 需要有效的Google AI API密钥

## 版本历史

### v1.0.0 (2025-03-28)
- 初始版本发布
- 支持课程管理、文件上传和分析
- 支持智能问答与总结功能

### v1.1.0 (2025-03-29)
- 优化文件删除按钮样式
- 修复JSON解析错误
- 完善系统文档

### v1.2.0 (2025-03-29)
- 改进文件项UI布局
- 使删除按钮始终可见
- 增强整体可读性和结构

### v1.3.0 (2025-03-29)
- 优化界面布局比例，扩大回复内容区域
- 缩小左侧导航和文件上传区域宽度
- 调整文件项样式使其更紧凑美观
- 增加聊天消息区域的显示宽度

## 部署说明

### 1. Vercel部署（推荐）
1. **准备工作**
   - 注册Vercel账号
   - 安装Vercel CLI: `npm i -g vercel`

2. **部署步骤**
   ```bash
   # 登录Vercel
   vercel login
   
   # 部署项目
   vercel
   
   # 生产环境部署
   vercel --prod
   ```

3. **环境变量配置**
   - 在Vercel项目设置中添加以下环境变量：
     - `NEXT_PUBLIC_API_URL`: 你的API服务地址
     - `GOOGLE_AI_API_KEY`: Google AI API密钥
     - `NODE_ENV`: production

4. **自定义域名**
   - 在Vercel项目设置中添加你的域名
   - 按照Vercel的指引配置DNS记录

### 2. 传统部署（Docker方式）
- 安装 Docker 和 Docker Compose
- 准备域名和SSL证书
- 配置环境变量

### 2. 配置步骤
1. **克隆代码库**
   ```bash
   git clone <repository_url>
   cd <project_directory>
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入实际的配置值
   ```

3. **准备SSL证书**
   ```bash
   mkdir ssl
   # 将SSL证书复制到ssl目录
   cp your_cert.pem ssl/cert.pem
   cp your_key.pem ssl/key.pem
   ```

4. **构建和启动服务**
   ```bash
   docker-compose up -d
   ```

### 3. 维护说明
- **查看日志**
  ```bash
  docker-compose logs -f
  ```

- **更新应用**
  ```bash
  git pull
  docker-compose build
  docker-compose up -d
  ```

- **备份数据**
  ```bash
  docker-compose exec app tar -czf /backup/files.tar.gz /app/uploads
  ```

### 4. 性能优化
- Nginx配置了静态文件缓存
- 启用了Gzip压缩
- 配置了安全headers
- 使用HTTP/2协议
- 启用了SSL会话缓存

### 5. 安全建议
- 定期更新依赖包
- 使用强密码
- 启用防火墙
- 定期备份数据
- 监控系统资源使用

### 6. 故障排除
- 检查日志文件
- 验证环境变量
- 确认端口是否被占用
- 检查SSL证书有效性
- 验证文件权限
- 
### 7. 部署状态

- 前端: ![Vercel](https://img.shields.io/badge/vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white)
- 后端: ![Render](https://img.shields.io/badge/Render-%46E3B7.svg?style=for-the-badge&logo=render&logoColor=white)

最后更新: 2025-04-05
