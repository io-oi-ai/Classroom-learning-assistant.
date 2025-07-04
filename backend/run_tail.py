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
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                    elif file_type == 'audio':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
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
                        screenshots=None
                    )
                    
                    self.wfile.write(json.dumps({
                        "success": True,
                        "file": new_file,
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
            return
        
        # 其他POST请求的通用响应头设置
        print(f"POST请求路径: {self.path}")
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 更新课程名称 (需要在创建课程之前检查，因为路径更具体)
        if self.path.startswith('/api/courses/') and '/update' in self.path:
            print(f"更新课程路径匹配成功: {self.path}")
            try:
                # 解析URL: /api/courses/{course_id}/update
                parts = self.path.split('/')
                print(f"路径分割结果: {parts}")
                course_id = parts[3]
                print(f"课程ID: {course_id}")
                
                # 解析POST请求中的JSON数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', '').strip()
                
                if not name:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "课程名称不能为空"
                    }).encode('utf-8'))
                    return
                
                result = update_course(course_id, name)
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode('utf-8'))
        
        # 创建新课程
        elif self.path == '/api/courses':
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
        
        # 生成手写笔记
        elif self.path == '/api/generate-handwritten-note':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                content = data.get('content', '')
                course_id = data.get('courseId', '')
                
                if not content.strip():
                    self.wfile.write(json.dumps({
                        "error": "笔记内容不能为空"
                    }).encode('utf-8'))
                    return
                
                if not course_id:
                self.wfile.write(json.dumps({
                        "error": "课程ID不能为空"
                    }).encode('utf-8'))
                    return
                
                # 生成手写笔记图片
                image_url = self.generate_handwritten_note(content, course_id)
                
                if image_url:
                    self.wfile.write(json.dumps({
                        "success": True,
                        "imageUrl": image_url,
                        "message": "手写笔记生成成功"
                    }).encode('utf-8'))
                    else:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "手写笔记生成失败"
                    }).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": f"生成手写笔记时出错: {str(e)}"
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
        
        else:
            self.wfile.write(json.dumps({
                "error": "路径不存在"
            }).encode('utf-8'))

    def generate_handwritten_note(self, content, course_id):
        """生成手写风格的笔记图片"""
        try:
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            # 设置画布大小和颜色
            width, height = 800, 1000
            # 使用米白色背景，模拟纸张
            bg_color = (252, 248, 240)
            image = Image.new('RGB', (width, height), color=bg_color)
            draw = ImageDraw.Draw(image)
            
            # 尝试使用不同的字体
            try:
                # 尝试使用系统字体
                font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32)
                font_content = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 24)
                font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
            except:
                try:
                    font_title = ImageFont.truetype("Arial.ttf", 32)
                    font_content = ImageFont.truetype("Arial.ttf", 24)
                    font_small = ImageFont.truetype("Arial.ttf", 18)
                except:
                    font_title = ImageFont.load_default()
                    font_content = ImageFont.load_default()
                    font_small = ImageFont.load_default()
            
            # 设置颜色
            ink_blue = (25, 25, 112)  # 深蓝色，模拟钢笔墨水
            highlight_yellow = (255, 255, 0, 100)  # 半透明黄色高亮
            
            # 绘制笔记本线条（横线）
            line_color = (200, 200, 200)
            for y in range(80, height - 50, 40):
                draw.line([(50, y), (width - 50, y)], fill=line_color, width=1)
            
            # 绘制左边距线
            draw.line([(80, 50), (80, height - 50)], fill=(255, 182, 193), width=2)
            
            # 处理内容
            lines = content.split('\n')
            y_position = 60
            margin_left = 90
            
            for line in lines:
                if not line.strip():
                    y_position += 20
                    continue
                
                # 检查是否是标题（以#开头或全大写）
                if line.startswith('#') or (len(line) < 50 and line.isupper()):
                    # 绘制标题
                    title_text = line.replace('#', '').strip()
                    draw.text((margin_left, y_position), title_text, font=font_title, fill=ink_blue)
                    # 在标题下画下划线
                    title_width = draw.textlength(title_text, font=font_title)
                    draw.line([(margin_left, y_position + 35), (margin_left + title_width, y_position + 35)], 
                             fill=ink_blue, width=2)
                    y_position += 60
                
                # 检查是否是重点内容（包含★或重要关键词）
                elif '★' in line or any(keyword in line for keyword in ['重点', '关键', '重要', '核心']):
                    # 绘制高亮背景
                    text_width = draw.textlength(line, font=font_content)
                    highlight_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    highlight_draw = ImageDraw.Draw(highlight_overlay)
                    highlight_draw.rectangle([(margin_left - 5, y_position - 2), 
                                            (margin_left + text_width + 5, y_position + 28)], 
                                           fill=highlight_yellow)
                    image = Image.alpha_composite(image.convert('RGBA'), highlight_overlay).convert('RGB')
                    draw = ImageDraw.Draw(image)
                    
                    # 绘制文本
                    draw.text((margin_left, y_position), line, font=font_content, fill=ink_blue)
                    y_position += 40
                
                else:
                    # 普通文本，进行换行处理
                    wrapped_lines = textwrap.wrap(line, width=35)
                    for wrapped_line in wrapped_lines:
                        if y_position > height - 100:  # 防止超出画布
                            break
                        draw.text((margin_left, y_position), wrapped_line, font=font_content, fill=ink_blue)
                        y_position += 35
                
                if y_position > height - 100:  # 防止超出画布
                    break
            
            # 添加一些手写风格的装饰元素
            # 绘制一些小圆点作为装饰
            for i in range(3):
                x = margin_left + i * 20
                y = y_position + 20
                draw.ellipse([(x, y), (x + 4, y + 4)], fill=ink_blue)
            
            # 添加日期和页码
            import datetime
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            draw.text((width - 150, height - 30), date_str, font=font_small, fill=(128, 128, 128))
            draw.text((width - 50, height - 30), "1", font=font_small, fill=(128, 128, 128))
            
            # 保存图像
            image_filename = f"handwritten_note_{int(time.time())}.png"
            image_path = os.path.join(course_img_dir, image_filename)
            image.save(image_path, "PNG")
            
            # 返回相对URL路径
            return f"/uploads/{course_id}/images/{image_filename}"
                
            except Exception as e:
            print(f"生成手写笔记失败: {str(e)}")
            return None
    
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
                return self.generate_educational_card("知识点配图", content, course_id)
            else:
                print(f"图像生成API错误: {response.status_code}")
                return self.generate_educational_card("知识点配图", content, course_id)
        
        except Exception as e:
            print(f"生成图像时出错: {str(e)}")
            return self.generate_educational_card("知识点配图", content, course_id)
    
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
    
    def generate_educational_card(self, title, content, course_id):
        """生成高质量的教育知识卡片"""
        print(f"开始生成教育卡片 - 标题: {title[:50]}...")
        print(f"内容长度: {len(content)} 字符")
        try:
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            # 设置画布大小 - 适合多知识点显示，增加高度
            width, height = 1000, 1200
            
            # 创建渐变背景 - 从浅蓝到白色的学术风格
            image = Image.new('RGB', (width, height), color=(245, 250, 255))
            draw = ImageDraw.Draw(image)
            
            # 绘制渐变背景
            for y in range(height):
                color_ratio = y / height
                r = int(245 + (255 - 245) * color_ratio)
                g = int(250 + (255 - 250) * color_ratio)
                b = int(255)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # 设置字体 - 优先使用支持中文的字体
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Helvetica.ttc", 
                "/System/Library/Fonts/Arial Unicode MS.ttf",
                "Arial.ttf"
            ]
            
            fonts_loaded = False
            for font_path in font_paths:
                try:
                    font_title = ImageFont.truetype(font_path, 32)
                    font_subtitle = ImageFont.truetype(font_path, 18)
                    font_content = ImageFont.truetype(font_path, 14)
                    font_small = ImageFont.truetype(font_path, 12)
                    fonts_loaded = True
                    print(f"成功加载字体: {font_path}")
                    break
            except:
                    continue
            
            if not fonts_loaded:
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
                font_content = ImageFont.load_default()
                font_small = ImageFont.load_default()
                print("使用默认字体")
            
            # 定义颜色方案
            primary_color = (44, 62, 80)      # 深蓝灰
            accent_color = (52, 152, 219)     # 蓝色
            highlight_color = (231, 76, 60)   # 红色
            text_color = (52, 73, 94)         # 深灰
            light_text = (127, 140, 141)      # 浅灰
            
            # 绘制顶部装饰条
            draw.rectangle([(0, 0), (width, 8)], fill=accent_color)
            
            # 绘制标题背景
            title_bg_height = 80
            draw.rectangle([(0, 8), (width, title_bg_height)], fill=(236, 240, 241))
            
            # 绘制标题
            title_lines = textwrap.wrap(title, width=20)
            title_y = 25
            for line in title_lines:
                title_width = draw.textlength(line, font=font_title)
                title_x = (width - title_width) // 2
                draw.text((title_x, title_y), line, font=font_title, fill=primary_color)
                title_y += 40
            
            # 内容区域起始位置
            content_start_y = title_bg_height + 30
            margin_left = 60
            margin_right = 60
            content_width = width - margin_left - margin_right
            
            # 解析内容结构
            content_lines = content.split('\n')
            current_y = content_start_y
            
            # 识别关键词并高亮显示
            keywords = ['定义', '概念', '原理', '应用', '例如', '重要', '核心', '关键', '学习要点', '注意', '方法', '步骤', '过程', '结论', '总结']
            
            for line in content_lines:
                if not line.strip():
                    current_y += 15
                    continue
                
                # 检查是否是知识点标题（以数字开头）或包含关键词的要点行
                is_numbered_point = line.strip().startswith(tuple('123456789'))
                is_key_point = any(keyword in line for keyword in keywords) or is_numbered_point
                
                if is_key_point:
                    # 绘制要点背景
                    point_height = 25
                    draw.rectangle([(margin_left - 10, current_y - 5), 
                                  (width - margin_right + 10, current_y + point_height)], 
                                 fill=(241, 196, 15, 50))  # 半透明黄色
                    
                    # 绘制要点标记
                    draw.ellipse([(margin_left - 25, current_y + 5), 
                                 (margin_left - 15, current_y + 15)], 
                                fill=highlight_color)
                
                # 文本换行处理 - 针对不同类型的行使用不同的换行宽度
                if is_numbered_point:
                    # 知识点标题使用更宽的换行
                    wrapped_lines = textwrap.wrap(line, width=60)
                else:
                    wrapped_lines = textwrap.wrap(line, width=55)
                    
                for wrapped_line in wrapped_lines:
                    if current_y > height - 150:  # 防止超出画布，增加底部边距
                        # 如果内容太长，添加省略号
                        draw.text((margin_left, current_y), "... (内容过长，已省略)", 
                                 font=font_small, fill=light_text)
                        break
                    
                    # 选择字体和颜色
                    if is_numbered_point:
                        current_font = font_subtitle
                        current_color = highlight_color  # 知识点标题使用更醒目的颜色
                    elif is_key_point:
                        current_font = font_subtitle
                        current_color = primary_color
                    else:
                        current_font = font_content
                        current_color = text_color
                    
                    draw.text((margin_left, current_y), wrapped_line, 
                             font=current_font, fill=current_color)
                    current_y += 30 if is_numbered_point else (25 if is_key_point else 22)
                
                # 知识点之间增加更多间距
                current_y += 15 if is_numbered_point else 8
            
            # 绘制知识点连接图示（如果内容中有多个相关概念）
            self.draw_knowledge_diagram(draw, content, width, height, accent_color, text_color)
            
            # 绘制装饰元素
            # 右上角学科图标区域
            icon_size = 80
            icon_x = width - icon_size - 30
            icon_y = title_bg_height + 20
            
            # 绘制图标背景圆
            draw.ellipse([(icon_x, icon_y), (icon_x + icon_size, icon_y + icon_size)], 
                        fill=accent_color)
            
            # 根据内容类型绘制不同的图标
            self.draw_subject_icon(draw, title + content, icon_x, icon_y, icon_size)
            
            # 绘制底部装饰
            # 左下角装饰三角形
            triangle_points = [(0, height), (0, height-40), (40, height)]
            draw.polygon(triangle_points, fill=accent_color)
            
            # 右下角时间戳
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
            draw.text((width - 120, height - 25), f"生成于 {timestamp}", 
                     font=font_small, fill=light_text)
            
            # 左下角学习提示
            draw.text((20, height - 25), "💡 重点内容已高亮标注", 
                     font=font_small, fill=light_text)
            
            # 保存图像
            image_filename = f"knowledge_card_{int(time.time())}.png"
            image_path = os.path.join(course_img_dir, image_filename)
            image.save(image_path, "PNG", quality=95)
            
            # 返回相对URL路径
            return f"/uploads/{course_id}/images/{image_filename}"
            
        except Exception as e:
            print(f"生成教育卡片失败: {str(e)}")
            return self.generate_simple_fallback(title, content, course_id)
    
    def generate_test_card(self, title, content, course_id):
        """生成优化的笔记卡片，支持中文、数学公式和图形"""
        try:
            print(f"=== 智能卡片生成 ===")
            print(f"标题: {title}")
            print(f"内容长度: {len(content)} 字符")
            
            # 创建课程图片目录
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            # 创建高质量卡片
            width, height = 900, 1200
            image = Image.new('RGB', (width, height), color=(248, 250, 252))
            draw = ImageDraw.Draw(image)
            
            # 绘制渐变背景
            for y in range(height):
                ratio = y / height
                r = int(248 + (255 - 248) * ratio)
                g = int(250 + (255 - 250) * ratio)  
                b = int(252 + (255 - 252) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            # 加载最佳中文字体
            font_title, font_content, font_small = self.load_chinese_fonts()
            
            # 绘制卡片主体
            card_margin = 20
            card_x1, card_y1 = card_margin, card_margin
            card_x2, card_y2 = width - card_margin, height - card_margin
            
            # 卡片阴影效果
            shadow_offset = 5
            draw.rectangle([(card_x1 + shadow_offset, card_y1 + shadow_offset), 
                           (card_x2 + shadow_offset, card_y2 + shadow_offset)], 
                          fill=(200, 200, 200, 100))
            
            # 卡片主体
            draw.rectangle([(card_x1, card_y1), (card_x2, card_y2)], 
                          fill=(255, 255, 255), outline=(220, 220, 220), width=2)
            
            # 标题区域
            title_height = 80
            draw.rectangle([(card_x1, card_y1), (card_x2, card_y1 + title_height)], 
                          fill=(59, 130, 246))  # 蓝色标题背景
            
            # 绘制标题
            title_y = card_y1 + 25
            title_lines = self.smart_text_wrap(title, 28)
            for line in title_lines:
                try:
                    title_width = draw.textlength(line, font=font_title)
                except:
                    title_width = len(line) * 16  # 备选计算
                title_x = (width - title_width) // 2
                self.safe_draw_text(draw, line, (title_x, title_y), font_title, (255, 255, 255))
                title_y += 35
            
            # 内容区域
            content_y = card_y1 + title_height + 30
            content_margin = 40
            
            # 检测学科类型并绘制对应的专业内容
            subject_type = self.detect_subject_type(content)
            
            if subject_type == 'math':
                content_y = self.draw_math_content(draw, content, content_margin, content_y, 
                                                 width - 2 * content_margin, font_content, font_small)
            elif subject_type == 'biology':
                content_y = self.draw_biology_content(draw, content, content_margin, content_y, 
                                                    width - 2 * content_margin, font_content, font_small)
            elif subject_type == 'chemistry':
                content_y = self.draw_chemistry_content(draw, content, content_margin, content_y, 
                                                      width - 2 * content_margin, font_content, font_small)
            elif subject_type == 'physics':
                content_y = self.draw_physics_content(draw, content, content_margin, content_y, 
                                                    width - 2 * content_margin, font_content, font_small)
            elif subject_type == 'history':
                content_y = self.draw_history_content(draw, content, content_margin, content_y, 
                                                    width - 2 * content_margin, font_content, font_small)
            elif subject_type == 'language':
                content_y = self.draw_language_content(draw, content, content_margin, content_y, 
                                                     width - 2 * content_margin, font_content, font_small)
            else:
                content_y = self.draw_regular_content(draw, content, content_margin, content_y, 
                                                    width - 2 * content_margin, font_content)
            
            # 底部信息
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            draw.text((content_margin, height - 50), f"生成时间: {timestamp}", 
                     font=font_small, fill=(128, 128, 128))
            
            # 添加下载标识
            draw.text((width - 200, height - 50), "📥 支持下载", 
                     font=font_small, fill=(59, 130, 246))
            
            # 保存图像
            image_filename = f"smart_card_{int(time.time())}.png"
            image_path = os.path.join(course_img_dir, image_filename)
            image.save(image_path, "PNG", quality=95)
            
            print(f"✅ 智能卡片生成成功: {image_path}")
            
            # 返回相对URL路径
            return f"/uploads/{course_id}/images/{image_filename}"
            
        except Exception as e:
            print(f"❌ 智能卡片生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def load_chinese_fonts(self):
        """加载最佳的中文字体"""
        # 根据测试结果，优先使用已验证可用的字体
        font_paths = [
            # 已验证可用的macOS字体（按优先级排序）
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc", 
            "/System/Library/Fonts/Helvetica.ttc",
            
            # 备选字体路径
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
            "/Library/Fonts/Arial Unicode MS.ttf",
            
            # 常见的字体文件名
            "STHeiti.ttc",
            "Hiragino Sans GB.ttc",
            "PingFang.ttc",
            "Arial Unicode MS.ttf",
            
            # 相对路径
            "../fonts/STHeiti.ttc",
            "./fonts/Arial.ttf"
        ]
        
        for font_path in font_paths:
            try:
                # 测试字体是否支持中文
                test_font = ImageFont.truetype(font_path, 20)
                
                # 创建测试图像来验证中文支持
                test_img = Image.new('RGB', (100, 50), color=(255, 255, 255))
                test_draw = ImageDraw.Draw(test_img)
                
                # 尝试绘制中文字符
                test_text = "测试中文"
                test_draw.text((10, 10), test_text, font=test_font, fill=(0, 0, 0))
                
                # 如果没有异常，说明字体支持中文
                font_title = ImageFont.truetype(font_path, 28)
                font_content = ImageFont.truetype(font_path, 18)
                font_small = ImageFont.truetype(font_path, 14)
                
                print(f"✅ 成功加载并验证中文字体: {font_path}")
                return font_title, font_content, font_small
                
            except Exception as e:
                print(f"⚠️ 字体加载或验证失败 {font_path}: {e}")
                continue
        
        # 如果所有字体都失败，尝试使用系统默认字体但增加大小
        print("⚠️ 所有专用字体加载失败，使用默认字体")
        try:
            # 尝试加载默认字体的不同大小
            default_title = ImageFont.load_default()
            default_content = ImageFont.load_default() 
            default_small = ImageFont.load_default()
            
            return default_title, default_content, default_small
        except:
            # 最后的备选方案
            print("❌ 使用PIL默认字体")
            from PIL import ImageFont
            default_font = ImageFont.load_default()
            return default_font, default_font, default_font

    def smart_text_wrap(self, text, max_width):
        """智能文本换行，支持中文"""
        if not text:
            return []
        
        lines = []
        current_line = ""
        char_count = 0
        
        for char in text:
            # 中文字符占用2个字符宽度，英文字符占用1个
            char_width = 2 if ord(char) > 127 else 1
            
            if char_count + char_width > max_width:
                if current_line:  # 如果当前行不为空，先保存
                    lines.append(current_line)
                    current_line = char
                    char_count = char_width
                else:  # 如果当前行为空但字符太长，强制换行
                    current_line = char
                    char_count = char_width
            else:
                current_line += char
                char_count += char_width
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def detect_subject_type(self, content):
        """检测内容属于哪个学科类型"""
        content_lower = content.lower()
        
        # 数学
        math_keywords = [
            '函数', 'function', '极限', 'limit', '导数', 'derivative',
            '积分', 'integral', '方程', 'equation', 'f(x)', 'y=',
            'sin', 'cos', 'tan', 'log', 'ln', '∫', '∑', '√', '数学'
        ]
        
        # 生物学
        biology_keywords = [
            '细胞', 'cell', 'dna', 'rna', '基因', 'gene', '蛋白质', 'protein',
            '细胞膜', '细胞核', '线粒体', '叶绿体', '染色体', '酶', 'enzyme',
            '生物', '遗传', '进化', '生态', '植物', '动物', '微生物',
            '细胞壁', '核糖体', '内质网', '高尔基体'
        ]
        
        # 化学
        chemistry_keywords = [
            '分子', 'molecule', '原子', 'atom', '化学键', '离子', 'ion',
            '化学反应', '化合物', '元素', 'element', '氧化', '还原',
            '酸', '碱', 'ph', '催化剂', '有机', '无机', '化学',
            '电子', '质子', '中子', '周期表', '共价键', '离子键'
        ]
        
        # 物理学
        physics_keywords = [
            '力', 'force', '能量', 'energy', '速度', 'velocity', '加速度',
            '电流', '电压', '电阻', '磁场', '重力', '摩擦力',
            '波', 'wave', '频率', '振动', '光', '热', '物理',
            '牛顿', '动量', '功率', '压强', '温度'
        ]
        
        # 历史
        history_keywords = [
            '历史', 'history', '朝代', '年代', '事件', '战争', '革命',
            '皇帝', '国王', '政治', '文化', '社会', '经济发展',
            '古代', '近代', '现代', '时间线', '历史背景'
        ]
        
        # 语言文学
        language_keywords = [
            '语法', 'grammar', '词汇', '语言', '文学', '诗歌', '散文',
            '语音', '语义', '句法', '修辞', '文字', '阅读', '写作',
            '语言学', '文学作品', '语言现象'
        ]
        
        # 按优先级检测
        if any(keyword in content_lower for keyword in biology_keywords):
            return 'biology'
        elif any(keyword in content_lower for keyword in chemistry_keywords):
            return 'chemistry'
        elif any(keyword in content_lower for keyword in physics_keywords):
            return 'physics'
        elif any(keyword in content_lower for keyword in math_keywords):
            return 'math'
        elif any(keyword in content_lower for keyword in history_keywords):
            return 'history'
        elif any(keyword in content_lower for keyword in language_keywords):
            return 'language'
        else:
            return 'general'

    def draw_math_content(self, draw, content, x, y, width, font_content, font_small):
        """绘制数学内容，包括函数图像"""
        try:
            # 分析是否包含函数
            if 'f(x)' in content or 'y=' in content:
                # 绘制坐标系和函数图像
                y = self.draw_coordinate_system(draw, x, y, width, content)
                y += 20
            
            # 绘制文本内容
            lines = content.split('\n')
            for line in lines:
                if not line.strip():
                    y += 15
                    continue
                
                # 检测数学公式行
                if any(symbol in line for symbol in ['=', '∫', '∑', '√', 'lim']):
                    # 使用特殊颜色绘制公式
                    wrapped_lines = self.smart_text_wrap(line, 45)
                    for wrapped_line in wrapped_lines:
                        draw.text((x, y), wrapped_line, font=font_content, fill=(220, 38, 127))  # 粉红色
                        y += 25
                else:
                    # 普通文本
                    wrapped_lines = self.smart_text_wrap(line, 45)
                    for wrapped_line in wrapped_lines:
                        draw.text((x, y), wrapped_line, font=font_content, fill=(51, 65, 85))
                        y += 23
                
                y += 5
                
        except Exception as e:
            print(f"绘制数学内容失败: {e}")
        
        return y

    def draw_coordinate_system(self, draw, x, y, width, content):
        """绘制坐标系和函数图像"""
        try:
            # 坐标系区域
            coord_width = min(300, width - 40)
            coord_height = 200
            coord_x = x + 20
            coord_y = y + 20
            
            # 绘制坐标系背景
            draw.rectangle([(coord_x - 10, coord_y - 10), 
                           (coord_x + coord_width + 10, coord_y + coord_height + 10)], 
                          fill=(240, 249, 255), outline=(59, 130, 246), width=1)
            
            # 绘制坐标轴
            center_x = coord_x + coord_width // 2
            center_y = coord_y + coord_height // 2
            
            # X轴
            draw.line([(coord_x, center_y), (coord_x + coord_width, center_y)], 
                     fill=(99, 102, 241), width=2)
            # Y轴
            draw.line([(center_x, coord_y), (center_x, coord_y + coord_height)], 
                     fill=(99, 102, 241), width=2)
            
            # 绘制网格
            for i in range(1, 6):
                grid_x = coord_x + i * coord_width // 6
                grid_y = coord_y + i * coord_height // 6
                draw.line([(grid_x, coord_y), (grid_x, coord_y + coord_height)], 
                         fill=(200, 200, 200), width=1)
                draw.line([(coord_x, grid_y), (coord_x + coord_width, grid_y)], 
                         fill=(200, 200, 200), width=1)
            
            # 尝试绘制函数曲线
            self.draw_function_curve(draw, coord_x, coord_y, coord_width, coord_height, content)
            
            return y + coord_height + 40
            
        except Exception as e:
            print(f"绘制坐标系失败: {e}")
            return y + 50

    def draw_function_curve(self, draw, coord_x, coord_y, coord_width, coord_height, content):
        """绘制函数曲线"""
        try:
            import math
            
            # 简单的函数识别和绘制
            center_x = coord_x + coord_width // 2
            center_y = coord_y + coord_height // 2
            
            points = []
            
            # 根据内容判断函数类型
            if '二次函数' in content or 'x²' in content or 'x^2' in content:
                # 绘制抛物线 y = x²
                for i in range(-100, 101, 5):
                    x = i / 20  # 缩放
                    y = x * x / 4  # y = x²/4
                    screen_x = center_x + x * 20
                    screen_y = center_y - y * 20
                    if coord_x <= screen_x <= coord_x + coord_width and coord_y <= screen_y <= coord_y + coord_height:
                        points.append((screen_x, screen_y))
                        
            elif 'sin' in content or '正弦' in content:
                # 绘制正弦函数
                for i in range(-100, 101, 2):
                    x = i / 20
                    y = math.sin(x) * 50
                    screen_x = center_x + x * 20
                    screen_y = center_y - y
                    if coord_x <= screen_x <= coord_x + coord_width and coord_y <= screen_y <= coord_y + coord_height:
                        points.append((screen_x, screen_y))
                        
            elif 'cos' in content or '余弦' in content:
                # 绘制余弦函数
                for i in range(-100, 101, 2):
                    x = i / 20
                    y = math.cos(x) * 50
                    screen_x = center_x + x * 20
                    screen_y = center_y - y
                    if coord_x <= screen_x <= coord_x + coord_width and coord_y <= screen_y <= coord_y + coord_height:
                        points.append((screen_x, screen_y))
                        
            elif 'log' in content or '对数' in content:
                # 绘制对数函数
                for i in range(1, 101, 2):
                    x = i / 20
                    y = math.log(x) * 30
                    screen_x = center_x + x * 20
                    screen_y = center_y - y
                    if coord_x <= screen_x <= coord_x + coord_width and coord_y <= screen_y <= coord_y + coord_height:
                        points.append((screen_x, screen_y))
            else:
                # 默认绘制线性函数 y = x
                for i in range(-50, 51, 5):
                    x = i
                    y = i
                    screen_x = center_x + x * 2
                    screen_y = center_y - y * 2
                    if coord_x <= screen_x <= coord_x + coord_width and coord_y <= screen_y <= coord_y + coord_height:
                        points.append((screen_x, screen_y))
            
            # 绘制曲线
            if len(points) > 1:
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i + 1]], fill=(220, 38, 127), width=3)
                    
        except Exception as e:
            print(f"绘制函数曲线失败: {e}")

    def draw_regular_content(self, draw, content, x, y, width, font_content):
        """绘制普通内容"""
        try:
            lines = content.split('\n')
            
            for line in lines:
                if not line.strip():
                    y += 15
                    continue
                
                # 检测重要内容并高亮
                if any(keyword in line for keyword in ['重点', '重要', '关键', '核心', '定义']):
                    # 绘制高亮背景
                    text_width = draw.textlength(line[:40], font=font_content)
                    draw.rectangle([(x - 5, y - 2), (x + text_width + 5, y + 22)], 
                                 fill=(254, 240, 138, 150))  # 半透明黄色
                
                wrapped_lines = self.smart_text_wrap(line, 40)
                for wrapped_line in wrapped_lines:
                    self.safe_draw_text(draw, wrapped_line, (x, y), font_content, (51, 65, 85))
                    y += 23
                
                y += 5
                
        except Exception as e:
            print(f"绘制普通内容失败: {e}")
        
        return y

    def draw_biology_content(self, draw, content, x, y, width, font_content, font_small):
        """绘制生物学内容，包括细胞结构、DNA等"""
        try:
            # 检测是否需要绘制生物图像
            if any(keyword in content.lower() for keyword in ['细胞', 'cell', 'dna', '基因', '蛋白质']):
                if '细胞' in content.lower() or 'cell' in content.lower():
                    y = self.draw_cell_structure(draw, x, y, width, content)
                    y += 20
                elif 'dna' in content.lower() or '基因' in content.lower():
                    y = self.draw_dna_structure(draw, x, y, width, content)
                    y += 20
            
            # 绘制生物学文本内容
            y = self.draw_specialized_text(draw, content, x, y, width, font_content, 
                                         [(34, 139, 34), (0, 128, 0), (107, 142, 35)])  # 绿色系
            
        except Exception as e:
            print(f"绘制生物学内容失败: {e}")
        
        return y

    def draw_chemistry_content(self, draw, content, x, y, width, font_content, font_small):
        """绘制化学内容，包括分子结构、化学反应等"""
        try:
            # 检测是否需要绘制化学图像
            if any(keyword in content.lower() for keyword in ['分子', 'molecule', '原子', '化学反应']):
                if '分子' in content.lower() or 'molecule' in content.lower():
                    y = self.draw_molecule_structure(draw, x, y, width, content)
                    y += 20
                elif '化学反应' in content.lower():
                    y = self.draw_chemical_reaction(draw, x, y, width, content)
                    y += 20
            
            # 绘制化学文本内容
            y = self.draw_specialized_text(draw, content, x, y, width, font_content,
                                         [(255, 69, 0), (255, 140, 0), (255, 165, 0)])  # 橙色系
            
        except Exception as e:
            print(f"绘制化学内容失败: {e}")
        
        return y

    def draw_physics_content(self, draw, content, x, y, width, font_content, font_small):
        """绘制物理学内容，包括力学图、波形图等"""
        try:
            # 检测是否需要绘制物理图像
            if any(keyword in content.lower() for keyword in ['力', 'force', '波', 'wave', '电路']):
                if '力' in content.lower() or 'force' in content.lower():
                    y = self.draw_force_diagram(draw, x, y, width, content)
                    y += 20
                elif '波' in content.lower() or 'wave' in content.lower():
                    y = self.draw_wave_diagram(draw, x, y, width, content)
                    y += 20
            
            # 绘制物理学文本内容
            y = self.draw_specialized_text(draw, content, x, y, width, font_content,
                                         [(30, 144, 255), (0, 191, 255), (135, 206, 250)])  # 蓝色系
            
        except Exception as e:
            print(f"绘制物理学内容失败: {e}")
        
        return y

    def draw_history_content(self, draw, content, x, y, width, font_content, font_small):
        """绘制历史内容，包括时间线、历史事件等"""
        try:
            # 检测是否需要绘制历史图像
            if any(keyword in content.lower() for keyword in ['时间', '年代', '朝代', '事件']):
                y = self.draw_timeline(draw, x, y, width, content)
                y += 20
            
            # 绘制历史文本内容
            y = self.draw_specialized_text(draw, content, x, y, width, font_content,
                                         [(139, 69, 19), (160, 82, 45), (205, 133, 63)])  # 褐色系
            
        except Exception as e:
            print(f"绘制历史内容失败: {e}")
        
        return y

    def draw_language_content(self, draw, content, x, y, width, font_content, font_small):
        """绘制语言文学内容，包括语法树、词汇关系等"""
        try:
            # 检测是否需要绘制语言图像
            if any(keyword in content.lower() for keyword in ['语法', 'grammar', '词汇', '句法']):
                y = self.draw_grammar_tree(draw, x, y, width, content)
                y += 20
            
            # 绘制语言学文本内容
            y = self.draw_specialized_text(draw, content, x, y, width, font_content,
                                         [(148, 0, 211), (138, 43, 226), (123, 104, 238)])  # 紫色系
            
        except Exception as e:
            print(f"绘制语言学内容失败: {e}")
        
        return y

    def safe_draw_text(self, draw, text, position, font, fill):
        """安全的文本绘制函数，处理字体不支持的字符"""
        try:
            # 尝试直接绘制
            draw.text(position, text, font=font, fill=fill)
        except Exception as e:
            print(f"字体绘制失败，尝试替换特殊字符: {e}")
            try:
                # 替换可能导致问题的字符
                safe_text = text
                # 替换常见的特殊字符
                replacements = {
                    '★': '*',
                    '●': '·',
                    '◆': '◇',
                    '▲': '△',
                    '■': '□'
                }
                for old, new in replacements.items():
                    safe_text = safe_text.replace(old, new)
                
                draw.text(position, safe_text, font=font, fill=fill)
            except Exception as e2:
                print(f"安全文本绘制也失败，使用ASCII替代: {e2}")
                # 最后的备选方案：只保留ASCII字符
                ascii_text = ''.join(char if ord(char) < 128 else '?' for char in text)
                draw.text(position, ascii_text, font=font, fill=fill)

    def draw_specialized_text(self, draw, content, x, y, width, font_content, color_scheme):
        """绘制带有学科特色的文本内容"""
        try:
            lines = content.split('\n')
            primary_color, secondary_color, highlight_color = color_scheme
            
            for line in lines:
                if not line.strip():
                    y += 15
                    continue
                
                # 检测重要概念并使用不同颜色
                if any(keyword in line for keyword in ['定义', '概念', '原理', '定律', '理论']):
                    # 绘制重要概念背景
                    try:
                        text_width = min(draw.textlength(line[:35], font=font_content), width - 10)
                    except:
                        text_width = min(len(line[:35]) * 12, width - 10)  # 备选计算方法
                    
                    draw.rectangle([(x - 5, y - 2), (x + text_width + 5, y + 22)], 
                                 fill=(*highlight_color, 50))  # 半透明背景
                    text_color = primary_color
                elif any(keyword in line for keyword in ['例如', '比如', '举例', '实例']):
                    text_color = secondary_color
                else:
                    text_color = (51, 65, 85)  # 默认文本颜色
                
                wrapped_lines = self.smart_text_wrap(line, 40)
                for wrapped_line in wrapped_lines:
                    self.safe_draw_text(draw, wrapped_line, (x, y), font_content, text_color)
                    y += 23
                
                y += 5
                
        except Exception as e:
            print(f"绘制专业文本失败: {e}")
        
        return y

    def generate_simple_fallback(self, title, content, course_id):
        """简化版备选方案"""
        try:
            course_img_dir = os.path.join(UPLOAD_DIR, course_id, 'images')
            if not os.path.exists(course_img_dir):
                os.makedirs(course_img_dir)
            
            # 简单的白色背景卡片
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # 基础字体
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
                font_content = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
            except:
                font_title = ImageFont.load_default()
                font_content = ImageFont.load_default()
            
            # 绘制边框
            draw.rectangle([(10, 10), (width-10, height-10)], outline=(200, 200, 200), width=2)
            
            # 绘制标题
            title_wrapped = textwrap.wrap(title, width=25)
            y_pos = 30
            for line in title_wrapped:
                draw.text((30, y_pos), line, font=font_title, fill=(50, 50, 50))
                y_pos += 35
            
            # 绘制内容
            y_pos += 20
            content_lines = textwrap.wrap(content[:400], width=35)
            for line in content_lines:
                if y_pos > height - 50:
                    break
                draw.text((30, y_pos), line, font=font_content, fill=(80, 80, 80))
                y_pos += 25
            
            # 保存图像
            image_filename = f"simple_card_{int(time.time())}.png"
            image_path = os.path.join(course_img_dir, image_filename)
            image.save(image_path)
            
            return f"/uploads/{course_id}/images/{image_filename}"
            
        except Exception as e:
            print(f"简化版卡片生成失败: {str(e)}")
            return None
    
    def draw_knowledge_diagram(self, draw, content, width, height, accent_color, text_color):
        """绘制知识点连接图示"""
        try:
            # 检查内容中是否包含多个概念，适合绘制连接图
            concept_indicators = ['与', '和', '关系', '联系', '对比', '区别', '相互', '影响', '导致', '原因', '结果']
            if not any(indicator in content for indicator in concept_indicators):
                return
            
            # 在左侧绘制简单的概念连接图
            diagram_x = 50
            diagram_y = height - 200
            diagram_width = 200
            diagram_height = 120
            
            # 绘制三个概念节点
            node_radius = 25
            nodes = [
                (diagram_x + 30, diagram_y + 30),      # 左上
                (diagram_x + 170, diagram_y + 30),     # 右上  
                (diagram_x + 100, diagram_y + 90)      # 下方
            ]
            
            # 绘制连接线
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    draw.line([nodes[i], nodes[j]], fill=accent_color, width=2)
            
            # 绘制节点
            for i, (x, y) in enumerate(nodes):
                draw.ellipse([(x - node_radius, y - node_radius), 
                             (x + node_radius, y + node_radius)], 
                            fill=(255, 255, 255), outline=accent_color, width=3)
                
                # 在节点中绘制字母标识
                labels = ['A', 'B', 'C']
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 16)
                except:
                    font = ImageFont.load_default()
                
                text_width = draw.textlength(labels[i], font=font)
                text_x = x - text_width // 2
                text_y = y - 8
                draw.text((text_x, text_y), labels[i], font=font, fill=text_color)
                
        except Exception as e:
            print(f"绘制知识点图示失败: {str(e)}")
    
    def draw_subject_icon(self, draw, text_content, icon_x, icon_y, icon_size):
        """根据内容类型绘制不同的学科图标"""
        try:
            # 根据内容判断学科类型
            if any(keyword in text_content for keyword in ['数学', '函数', '极限', '导数', '积分', '公式', '方程']):
                self.draw_math_icon(draw, icon_x, icon_y, icon_size)
            elif any(keyword in text_content for keyword in ['物理', '力学', '电学', '光学', '波动', '能量']):
                self.draw_physics_icon(draw, icon_x, icon_y, icon_size)
            elif any(keyword in text_content for keyword in ['化学', '反应', '分子', '原子', '化合物', '元素']):
                self.draw_chemistry_icon(draw, icon_x, icon_y, icon_size)
            elif any(keyword in text_content for keyword in ['生物', '细胞', '基因', '蛋白质', '生物学']):
                self.draw_biology_icon(draw, icon_x, icon_y, icon_size)
            elif any(keyword in text_content for keyword in ['历史', '文化', '社会', '政治', '经济']):
                self.draw_humanities_icon(draw, icon_x, icon_y, icon_size)
            else:
                # 默认书本图标
                self.draw_book_icon(draw, icon_x, icon_y, icon_size)
                
        except Exception as e:
            print(f"绘制学科图标失败: {str(e)}")
            self.draw_book_icon(draw, icon_x, icon_y, icon_size)
    
    def draw_math_icon(self, draw, icon_x, icon_y, icon_size):
        """绘制数学图标"""
        margin = 15
        # 绘制函数曲线 y = x²
        points = []
        for i in range(21):
            x = icon_x + margin + (icon_size - 2 * margin) * i / 20
            # 简化的抛物线
            y_offset = ((i - 10) / 10) ** 2 * 20
            y = icon_y + icon_size - margin - y_offset
            points.append((x, y))
        
        # 绘制曲线
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=(255, 255, 255), width=3)
        
        # 绘制坐标轴
        center_x = icon_x + icon_size // 2
        center_y = icon_y + icon_size // 2
        axis_length = 25
        
        # X轴
        draw.line([(center_x - axis_length, center_y + 10), 
                  (center_x + axis_length, center_y + 10)], 
                 fill=(255, 255, 255), width=2)
        # Y轴  
        draw.line([(center_x - 10, center_y - axis_length), 
                  (center_x - 10, center_y + axis_length)], 
                 fill=(255, 255, 255), width=2)
    
    def draw_physics_icon(self, draw, icon_x, icon_y, icon_size):
        """绘制物理图标（原子模型）"""
        center_x = icon_x + icon_size // 2
        center_y = icon_y + icon_size // 2
        
        # 绘制原子核
        nucleus_radius = 8
        draw.ellipse([(center_x - nucleus_radius, center_y - nucleus_radius),
                     (center_x + nucleus_radius, center_y + nucleus_radius)],
                    fill=(255, 255, 255))
        
        # 绘制电子轨道
        for radius in [20, 30, 40]:
            draw.ellipse([(center_x - radius, center_y - radius),
                         (center_x + radius, center_y + radius)],
                        outline=(255, 255, 255), width=2)
        
        # 绘制电子
        electron_positions = [(center_x + 30, center_y), (center_x - 25, center_y - 15)]
        for ex, ey in electron_positions:
            draw.ellipse([(ex - 4, ey - 4), (ex + 4, ey + 4)], fill=(255, 255, 255))
    
    def draw_chemistry_icon(self, draw, icon_x, icon_y, icon_size):
        """绘制化学图标（分子结构）"""
        center_x = icon_x + icon_size // 2
        center_y = icon_y + icon_size // 2
        
        # 绘制分子节点
        molecules = [
            (center_x - 20, center_y - 15),
            (center_x + 20, center_y - 15),
            (center_x, center_y + 15)
        ]
        
        # 绘制化学键
        for i in range(len(molecules)):
            for j in range(i + 1, len(molecules)):
                draw.line([molecules[i], molecules[j]], fill=(255, 255, 255), width=3)
        
        # 绘制原子
        for mx, my in molecules:
            draw.ellipse([(mx - 8, my - 8), (mx + 8, my + 8)], fill=(255, 255, 255))
    
    def draw_biology_icon(self, draw, icon_x, icon_y, icon_size):
        """绘制生物图标（DNA双螺旋）"""
        center_x = icon_x + icon_size // 2
        
        # 绘制DNA双螺旋结构
        for y_offset in range(0, icon_size - 20, 8):
            y = icon_y + 10 + y_offset
            angle = y_offset * 0.3
            
            # 左螺旋
            x1 = center_x - 15 + 10 * __import__('math').sin(angle)
            # 右螺旋
            x2 = center_x + 15 + 10 * __import__('math').sin(angle + __import__('math').pi)
            
            draw.ellipse([(x1 - 3, y - 3), (x1 + 3, y + 3)], fill=(255, 255, 255))
            draw.ellipse([(x2 - 3, y - 3), (x2 + 3, y + 3)], fill=(255, 255, 255))
            
            # 连接线
            if y_offset % 16 == 0:
                draw.line([(x1, y), (x2, y)], fill=(255, 255, 255), width=2)
    
    def draw_humanities_icon(self, draw, icon_x, icon_y, icon_size):
        """绘制人文图标（古建筑柱子）"""
        margin = 15
        col_width = 8
        col_height = icon_size - 2 * margin
        
        # 绘制三根柱子
        for i in range(3):
            x = icon_x + margin + i * (icon_size - 2 * margin) // 3
            # 柱身
            draw.rectangle([(x, icon_y + margin), (x + col_width, icon_y + margin + col_height)],
                          fill=(255, 255, 255))
            # 柱头
            draw.rectangle([(x - 3, icon_y + margin), (x + col_width + 3, icon_y + margin + 5)],
                          fill=(255, 255, 255))
            # 柱基
            draw.rectangle([(x - 2, icon_y + margin + col_height - 3), 
                          (x + col_width + 2, icon_y + margin + col_height)],
                          fill=(255, 255, 255))
    
    def draw_book_icon(self, draw, icon_x, icon_y, icon_size):
        """绘制默认书本图标"""
        book_margin = 20
        book_x1 = icon_x + book_margin
        book_y1 = icon_y + book_margin
        book_x2 = icon_x + icon_size - book_margin
        book_y2 = icon_y + icon_size - book_margin
        
        # 书本主体
        draw.rectangle([(book_x1, book_y1), (book_x2, book_y2)], 
                      fill=(255, 255, 255))
        draw.rectangle([(book_x1, book_y1), (book_x2, book_y2)], 
                      outline=(236, 240, 241), width=2)
        
        # 书本页面线条
        for i in range(3):
            line_y = book_y1 + 15 + i * 8
            draw.line([(book_x1 + 8, line_y), (book_x2 - 8, line_y)], 
                     fill=(200, 200, 200), width=1)

    # 学科专业图像绘制函数
    def draw_cell_structure(self, draw, x, y, width, content):
        """绘制细胞结构图"""
        try:
            # 细胞结构绘制区域
            cell_width = min(250, width - 40)
            cell_height = 180
            cell_x = x + 20
            cell_y = y + 20
            
            # 绘制细胞轮廓（椭圆形）
            draw.ellipse([(cell_x, cell_y), (cell_x + cell_width, cell_y + cell_height)], 
                        outline=(34, 139, 34), width=3, fill=(240, 255, 240))
            
            center_x = cell_x + cell_width // 2
            center_y = cell_y + cell_height // 2
            
            # 绘制细胞核
            nucleus_w, nucleus_h = 60, 45
            draw.ellipse([(center_x - nucleus_w//2, center_y - nucleus_h//2), 
                         (center_x + nucleus_w//2, center_y + nucleus_h//2)], 
                        outline=(0, 100, 0), width=2, fill=(220, 255, 220))
            
            # 绘制线粒体
            mito_positions = [(center_x - 80, center_y - 40), (center_x + 60, center_y + 30)]
            for mx, my in mito_positions:
                draw.ellipse([(mx - 15, my - 8), (mx + 15, my + 8)], 
                           outline=(0, 128, 0), width=1, fill=(200, 255, 200))
            
            # 添加标注
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
            except:
                font = ImageFont.load_default()
            
            draw.text((center_x - 20, center_y - 5), "细胞核", font=font, fill=(0, 100, 0))
            draw.text((center_x - 100, center_y - 50), "线粒体", font=font, fill=(0, 128, 0))
            
            return y + cell_height + 40
            
        except Exception as e:
            print(f"绘制细胞结构失败: {e}")
            return y + 50

    def draw_dna_structure(self, draw, x, y, width, content):
        """绘制DNA双螺旋结构"""
        try:
            import math
            
            # DNA结构绘制区域
            dna_width = min(200, width - 40)
            dna_height = 150
            dna_x = x + 20
            dna_y = y + 20
            
            # 绘制背景
            draw.rectangle([(dna_x - 10, dna_y - 10), 
                           (dna_x + dna_width + 10, dna_y + dna_height + 10)], 
                          fill=(248, 255, 248), outline=(34, 139, 34), width=1)
            
            center_x = dna_x + dna_width // 2
            
            # 绘制DNA双螺旋
            for i in range(0, dna_height, 8):
                y_pos = dna_y + i
                angle = i * 0.3
                
                # 左螺旋链
                x1 = center_x - 30 + 20 * math.sin(angle)
                # 右螺旋链
                x2 = center_x + 30 + 20 * math.sin(angle + math.pi)
                
                # 绘制核苷酸
                draw.ellipse([(x1 - 3, y_pos - 3), (x1 + 3, y_pos + 3)], fill=(0, 128, 0))
                draw.ellipse([(x2 - 3, y_pos - 3), (x2 + 3, y_pos + 3)], fill=(0, 128, 0))
                
                # 绘制氢键（连接线）
                if i % 16 == 0:
                    draw.line([(x1, y_pos), (x2, y_pos)], fill=(100, 149, 237), width=2)
            
            # 添加标注
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
            except:
                font = ImageFont.load_default()
            
            draw.text((dna_x, dna_y + dna_height + 15), "DNA双螺旋结构", font=font, fill=(0, 100, 0))
            
            return y + dna_height + 50
            
        except Exception as e:
            print(f"绘制DNA结构失败: {e}")
            return y + 50

    def draw_molecule_structure(self, draw, x, y, width, content):
        """绘制分子结构图"""
        try:
            # 分子结构绘制区域
            mol_width = min(220, width - 40)
            mol_height = 120
            mol_x = x + 20
            mol_y = y + 20
            
            # 绘制背景
            draw.rectangle([(mol_x - 10, mol_y - 10), 
                           (mol_x + mol_width + 10, mol_y + mol_height + 10)], 
                          fill=(255, 248, 240), outline=(255, 140, 0), width=1)
            
            center_x = mol_x + mol_width // 2
            center_y = mol_y + mol_height // 2
            
            # 绘制分子节点（原子）
            atoms = [
                (center_x - 60, center_y - 20, "C"),
                (center_x, center_y - 40, "H"),
                (center_x + 60, center_y - 20, "O"),
                (center_x, center_y + 20, "H")
            ]
            
            # 绘制化学键
            for i in range(len(atoms) - 1):
                x1, y1 = atoms[i][:2]
                x2, y2 = atoms[i + 1][:2]
                draw.line([(x1, y1), (x2, y2)], fill=(255, 69, 0), width=3)
            
            # 绘制原子
            colors = [(64, 64, 64), (255, 255, 255), (255, 0, 0), (255, 255, 255)]  # C黑 H白 O红
            for i, (ax, ay, symbol) in enumerate(atoms):
                draw.ellipse([(ax - 12, ay - 12), (ax + 12, ay + 12)], 
                           fill=colors[i], outline=(255, 140, 0), width=2)
                
                # 绘制元素符号
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 14)
                except:
                    font = ImageFont.load_default()
                
                text_color = (255, 255, 255) if symbol in ['C', 'O'] else (0, 0, 0)
                text_width = draw.textlength(symbol, font=font)
                draw.text((ax - text_width//2, ay - 6), symbol, font=font, fill=text_color)
            
            return y + mol_height + 40
            
        except Exception as e:
            print(f"绘制分子结构失败: {e}")
            return y + 50

    def draw_chemical_reaction(self, draw, x, y, width, content):
        """绘制化学反应式"""
        try:
            # 反应式绘制区域
            reaction_width = min(300, width - 40)
            reaction_height = 80
            reaction_x = x + 20
            reaction_y = y + 20
            
            # 绘制背景
            draw.rectangle([(reaction_x - 10, reaction_y - 10), 
                           (reaction_x + reaction_width + 10, reaction_y + reaction_height + 10)], 
                          fill=(255, 250, 240), outline=(255, 140, 0), width=1)
            
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 18)
                font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 14)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # 绘制反应式
            center_y = reaction_y + reaction_height // 2
            
            # 反应物
            draw.text((reaction_x + 10, center_y - 10), "A + B", font=font_large, fill=(255, 69, 0))
            
            # 箭头
            arrow_x = reaction_x + reaction_width // 2 - 20
            draw.line([(arrow_x, center_y), (arrow_x + 40, center_y)], fill=(255, 140, 0), width=3)
            draw.polygon([(arrow_x + 35, center_y - 5), (arrow_x + 40, center_y), (arrow_x + 35, center_y + 5)], 
                        fill=(255, 140, 0))
            
            # 产物
            draw.text((reaction_x + reaction_width - 80, center_y - 10), "C + D", font=font_large, fill=(255, 69, 0))
            
            # 条件标注
            draw.text((arrow_x + 5, center_y - 25), "催化剂", font=font_small, fill=(160, 82, 45))
            
            return y + reaction_height + 40
            
        except Exception as e:
            print(f"绘制化学反应失败: {e}")
            return y + 50

    def draw_force_diagram(self, draw, x, y, width, content):
        """绘制力学图"""
        try:
            # 力学图绘制区域
            force_width = min(200, width - 40)
            force_height = 150
            force_x = x + 20
            force_y = y + 20
            
            # 绘制背景
            draw.rectangle([(force_x - 10, force_y - 10), 
                           (force_x + force_width + 10, force_y + force_height + 10)], 
                          fill=(240, 248, 255), outline=(30, 144, 255), width=1)
            
            center_x = force_x + force_width // 2
            center_y = force_y + force_height // 2
            
            # 绘制物体（方块）
            obj_size = 30
            draw.rectangle([(center_x - obj_size//2, center_y - obj_size//2), 
                           (center_x + obj_size//2, center_y + obj_size//2)], 
                          fill=(135, 206, 250), outline=(30, 144, 255), width=2)
            
            # 绘制力矢量
            forces = [
                (center_x, center_y - obj_size//2 - 40, center_x, center_y - obj_size//2, "F₁"),  # 向上
                (center_x + obj_size//2 + 40, center_y, center_x + obj_size//2, center_y, "F₂"),  # 向右
                (center_x, center_y + obj_size//2 + 40, center_x, center_y + obj_size//2, "F₃")   # 向下
            ]
            
            for x1, y1, x2, y2, label in forces:
                # 绘制力矢量箭头
                draw.line([(x1, y1), (x2, y2)], fill=(255, 0, 0), width=3)
                
                # 绘制箭头头部
                if x1 == x2:  # 垂直箭头
                    if y1 < y2:  # 向下
                        draw.polygon([(x2 - 5, y2 - 8), (x2, y2), (x2 + 5, y2 - 8)], fill=(255, 0, 0))
                    else:  # 向上
                        draw.polygon([(x2 - 5, y2 + 8), (x2, y2), (x2 + 5, y2 + 8)], fill=(255, 0, 0))
                else:  # 水平箭头
                    draw.polygon([(x2 - 8, y2 - 5), (x2, y2), (x2 - 8, y2 + 5)], fill=(255, 0, 0))
                
                # 添加标签
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
                except:
                    font = ImageFont.load_default()
                
                label_x = x1 + (10 if x1 != x2 else 0)
                label_y = y1 + (10 if y1 != y2 else 0)
                draw.text((label_x, label_y), label, font=font, fill=(255, 0, 0))
            
            return y + force_height + 40
            
        except Exception as e:
            print(f"绘制力学图失败: {e}")
            return y + 50

    def draw_wave_diagram(self, draw, x, y, width, content):
        """绘制波形图"""
        try:
            import math
            
            # 波形图绘制区域
            wave_width = min(280, width - 40)
            wave_height = 120
            wave_x = x + 20
            wave_y = y + 20
            
            # 绘制背景
            draw.rectangle([(wave_x - 10, wave_y - 10), 
                           (wave_x + wave_width + 10, wave_y + wave_height + 10)], 
                          fill=(240, 248, 255), outline=(30, 144, 255), width=1)
            
            # 绘制坐标轴
            center_y = wave_y + wave_height // 2
            draw.line([(wave_x, center_y), (wave_x + wave_width, center_y)], 
                     fill=(100, 100, 100), width=2)  # X轴
            
            # 绘制波形
            points = []
            for i in range(wave_width):
                x_pos = wave_x + i
                # 正弦波
                wave_value = math.sin(i * 2 * math.pi / 60) * 30
                y_pos = center_y - wave_value
                points.append((x_pos, y_pos))
            
            # 绘制波形线
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill=(0, 191, 255), width=3)
            
            # 添加标注
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
            except:
                font = ImageFont.load_default()
            
            draw.text((wave_x, wave_y + wave_height + 15), "波形图", font=font, fill=(30, 144, 255))
            
            return y + wave_height + 40
            
        except Exception as e:
            print(f"绘制波形图失败: {e}")
            return y + 50

    def draw_timeline(self, draw, x, y, width, content):
        """绘制历史时间线"""
        try:
            # 时间线绘制区域
            timeline_width = min(350, width - 40)
            timeline_height = 100
            timeline_x = x + 20
            timeline_y = y + 20
            
            # 绘制背景
            draw.rectangle([(timeline_x - 10, timeline_y - 10), 
                           (timeline_x + timeline_width + 10, timeline_y + timeline_height + 10)], 
                          fill=(250, 245, 235), outline=(139, 69, 19), width=1)
            
            # 绘制时间线主轴
            line_y = timeline_y + timeline_height // 2
            draw.line([(timeline_x, line_y), (timeline_x + timeline_width, line_y)], 
                     fill=(160, 82, 45), width=4)
            
            # 绘制时间节点
            events = [
                (timeline_x + 50, "古代", "公元前"),
                (timeline_x + 150, "中世纪", "5-15世纪"),
                (timeline_x + 250, "近现代", "16-21世纪")
            ]
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
            except:
                font = ImageFont.load_default()
            
            for event_x, title, date in events:
                # 绘制时间节点
                draw.ellipse([(event_x - 8, line_y - 8), (event_x + 8, line_y + 8)], 
                           fill=(205, 133, 63), outline=(139, 69, 19), width=2)
                
                # 绘制垂直线
                draw.line([(event_x, line_y - 8), (event_x, timeline_y + 20)], 
                         fill=(160, 82, 45), width=2)
                
                # 添加标签
                draw.text((event_x - 20, timeline_y + 5), title, font=font, fill=(139, 69, 19))
                draw.text((event_x - 25, timeline_y + timeline_height - 25), date, 
                         font=font, fill=(160, 82, 45))
            
            return y + timeline_height + 40
            
        except Exception as e:
            print(f"绘制时间线失败: {e}")
            return y + 50

    def draw_grammar_tree(self, draw, x, y, width, content):
        """绘制语法树"""
        try:
            # 语法树绘制区域
            tree_width = min(250, width - 40)
            tree_height = 140
            tree_x = x + 20
            tree_y = y + 20
            
            # 绘制背景
            draw.rectangle([(tree_x - 10, tree_y - 10), 
                           (tree_x + tree_width + 10, tree_y + tree_height + 10)], 
                          fill=(248, 245, 255), outline=(148, 0, 211), width=1)
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 12)
            except:
                font = ImageFont.load_default()
            
            # 绘制语法树结构
            center_x = tree_x + tree_width // 2
            
            # 根节点
            root_y = tree_y + 20
            draw.rectangle([(center_x - 20, root_y - 10), (center_x + 20, root_y + 10)], 
                          fill=(238, 130, 238), outline=(148, 0, 211), width=2)
            draw.text((center_x - 8, root_y - 5), "句子", font=font, fill=(75, 0, 130))
            
            # 子节点
            child_y = tree_y + 60
            children = [
                (center_x - 60, "主语"),
                (center_x, "谓语"), 
                (center_x + 60, "宾语")
            ]
            
            for child_x, label in children:
                # 绘制连接线
                draw.line([(center_x, root_y + 10), (child_x, child_y - 10)], 
                         fill=(138, 43, 226), width=2)
                
                # 绘制子节点
                draw.rectangle([(child_x - 20, child_y - 10), (child_x + 20, child_y + 10)], 
                              fill=(221, 160, 221), outline=(148, 0, 211), width=1)
                text_width = draw.textlength(label, font=font)
                draw.text((child_x - text_width//2, child_y - 5), label, font=font, fill=(75, 0, 130))
            
            # 词汇节点
            word_y = tree_y + 100
            words = [
                (center_x - 60, "我"),
                (center_x, "学习"),
                (center_x + 60, "语言")
            ]
            
            for i, (word_x, word) in enumerate(words):
                child_x = children[i][0]
                # 绘制连接线
                draw.line([(child_x, child_y + 10), (word_x, word_y - 10)], 
                         fill=(138, 43, 226), width=1)
                
                # 绘制词汇
                draw.text((word_x - 10, word_y), word, font=font, fill=(123, 104, 238))
            
            return y + tree_height + 40
            
        except Exception as e:
            print(f"绘制语法树失败: {e}")
            return y + 50

    def do_DELETE(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 删除课程
        if self.path.startswith('/api/courses/') and not '/files/' in self.path and not '/cards' in self.path:
            # 解析URL: /api/courses/{course_id}
            parts = self.path.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                
                try:
                    result = delete_course(course_id)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
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
    
    def do_PUT(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 更新课程名称
        if self.path.startswith('/api/courses/') and not '/files/' in self.path and not '/cards' in self.path:
            # 解析URL: /api/courses/{course_id}
            parts = self.path.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                
                try:
                    # 读取请求数据
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    name = data.get('name', '').strip()
                    
                    if not name:
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": "课程名称不能为空"
                        }).encode('utf-8'))
                        return
                    
                    result = update_course(course_id, name)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                    
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "无效的更新请求路径"
                }).encode('utf-8'))
        
        else:
            self.wfile.write(json.dumps({
                "error": "不支持的请求地址"
            }).encode('utf-8'))

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
            
            # 添加文件内容到提示词
            for file in files:
                prompt += f"\n=== 文件: {file['name']} (类型: {file['type']}) ===\n"
                
                # 获取完整的文件内容摘要
                full_summary = file.get('summary', '无摘要')
                if len(full_summary) > 50:  # 如果摘要较长，使用完整内容
                    prompt += f"详细内容: {full_summary}\n"
                else:
                    prompt += f"内容摘要: {full_summary}\n"
                
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
            
            # 创建一张综合性的笔记卡片
            cards = []
            
            # 合并所有知识点为一张卡片
            if knowledge_points:
                # 使用第一个知识点的标题，或者创建一个综合标题
                main_title = f"{course.get('name', '课程')}核心知识点"
                
                # 合并所有知识点内容
                combined_content = ""
                for i, point in enumerate(knowledge_points, 1):
                    title = point.get("title", "未命名知识点")
                    content = point.get("content", "")
                    combined_content += f"{i}. {title}\n{content}\n\n"
                
                # 生成一张综合性的知识卡片配图（使用测试版本）
                print(f"生成卡片 - 标题: {main_title}")
                print(f"生成卡片 - 内容长度: {len(combined_content.strip())} 字符")
                print(f"生成卡片 - 内容预览: {combined_content.strip()[:200]}...")
                # 临时使用测试版本进行调试
                image_url = self.generate_test_card(main_title, combined_content.strip(), course_id)
                
                # 创建单张卡片
                card = {
                    "id": str(uuid.uuid4()),
                    "title": main_title,
                    "content": combined_content.strip(),
                    "image": image_url,
                    "course_id": course_id,
                    "file_ids": file_ids if file_ids else [file["id"] for file in files],
                    "created_at": int(time.time()),
                    "image_source": "generated" if image_url else "none"
                }
                cards.append(card)
            
            # 保存到数据库
            existing_cards = get_note_cards()
            all_cards = existing_cards + cards
            save_note_cards(all_cards)
            
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
    init_data_files()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'启动服务器在端口 {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run() 