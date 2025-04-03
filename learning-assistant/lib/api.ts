// API连接服务

export interface ChatResponse {
  response?: string;
  content?: string;
  error?: string;
}

// 发送聊天消息
export async function sendChatMessage(message: string): Promise<ChatResponse> {
  try {
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    
    return await response.json();
  } catch (error) {
    return { error: `发送失败: ${error.message}` };
  }
}

// 上传文件
export async function uploadFile(file: File, type: 'pdf' | 'audio' | 'video'): Promise<ChatResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`http://localhost:8000/api/upload/${type}`, {
      method: 'POST',
      body: formData,
    });
    
    return await response.json();
  } catch (error) {
    return { error: `上传失败: ${error.message}` };
  }
} 