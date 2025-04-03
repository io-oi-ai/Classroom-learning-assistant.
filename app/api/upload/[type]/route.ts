import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import path from 'path';
import { existsSync } from 'fs';
import * as os from 'os';

// 用于处理PDF的临时API调用
async function processPdf(filePath: string) {
  try {
    return await callGeminiMultimodalApi(filePath, 'pdf', '请分析这个PDF文件并提供详细信息和内容摘要。如果内容中包含问题，请回答这些问题。');
  } catch (error) {
    throw new Error(`PDF处理错误: ${error.message}`);
  }
}

// 调用Gemini多模态API
async function callGeminiMultimodalApi(filePath: string, fileType: string, prompt: string) {
  try {
    // 读取文件
    const fs = require('fs');
    const fileBuffer = fs.readFileSync(filePath);
    const fileBase64 = fileBuffer.toString('base64');
    
    // 确定MIME类型
    let mimeType = '';
    if (fileType === 'audio') {
      if (filePath.endsWith('.mp3')) mimeType = 'audio/mpeg';
      else if (filePath.endsWith('.wav')) mimeType = 'audio/wav';
      else if (filePath.endsWith('.m4a')) mimeType = 'audio/mp4';
      else mimeType = 'audio/mpeg';
    } else if (fileType === 'video') {
      if (filePath.endsWith('.mp4')) mimeType = 'video/mp4';
      else if (filePath.endsWith('.avi')) mimeType = 'video/x-msvideo';
      else if (filePath.endsWith('.mov')) mimeType = 'video/quicktime';
      else mimeType = 'video/mp4';
    } else if (fileType === 'pdf') {
      mimeType = 'application/pdf';
    }
    
    // 构建API请求
    const apiKey = process.env.GOOGLE_AI_API_KEY;
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [
              { text: `请用中文回答：${prompt}` },
              {
                inline_data: {
                  mime_type: mimeType,
                  data: fileBase64
                }
              }
            ]
          }],
          generationConfig: {
            temperature: 0.4,
            topK: 32,
            topP: 1,
            maxOutputTokens: 2048
          }
        })
      }
    );
    
    const result = await response.json();
    
    if (response.ok) {
      if (result.candidates && result.candidates.length > 0) {
        if (result.candidates[0].content && result.candidates[0].content.parts) {
          return result.candidates[0].content.parts[0].text;
        }
      }
      return "AI未能生成有效回复。这可能是因为文件过大或格式不受支持。";
    } else {
      return `API调用失败: HTTP ${response.status}\n${JSON.stringify(result)}\n\n这可能是因为文件太大或格式不受支持。`;
    }
  } catch (error) {
    return `处理${fileType}文件时出错: ${error.message}`;
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: { type: string } }
) {
  const fileType = params.type;
  
  // 验证文件类型
  if (!['pdf', 'audio', 'video'].includes(fileType)) {
    return NextResponse.json({ error: `不支持的文件类型: ${fileType}` }, { status: 400 });
  }
  
  try {
    // 创建临时上传目录
    const uploadDir = path.join(os.tmpdir(), 'learning-assistant-uploads');
    if (!existsSync(uploadDir)) {
      await mkdir(uploadDir, { recursive: true });
    }
    
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json({ error: "没有找到上传的文件" }, { status: 400 });
    }
    
    // 保存文件到临时目录
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    const filePath = path.join(uploadDir, `${Date.now()}_${file.name}`);
    await writeFile(filePath, buffer);
    
    // 根据文件类型处理
    let aiResponse;
    if (fileType === 'pdf') {
      aiResponse = await processPdf(filePath);
    } else if (fileType === 'audio') {
      aiResponse = await callGeminiMultimodalApi(filePath, 'audio', '请分析这个音频文件并提供详细内容描述、转录和总结');
    } else if (fileType === 'video') {
      aiResponse = await callGeminiMultimodalApi(filePath, 'video', '请分析这个视频并提供详细内容描述、场景分析、转录和总结');
    }
    
    // 删除临时文件
    const fs = require('fs');
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
    
    return NextResponse.json({ content: aiResponse });
  } catch (error) {
    return NextResponse.json({ error: `处理上传请求时出错: ${error.message}` }, { status: 500 });
  }
} 