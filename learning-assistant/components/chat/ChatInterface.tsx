"use client";

import { useState } from "react";
import { sendChatMessage, uploadFile } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Loader2, FileText, Music, Video } from "lucide-react";

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 处理发送消息
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;
    
    const newMessage: Message = {
      role: 'user',
      content: inputValue,
    };
    
    setMessages((prev) => [...prev, newMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await sendChatMessage(newMessage.content);
      
      if (response.error) {
        setError(response.error);
      } else if (response.response) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response.response },
        ]);
      }
    } catch (err) {
      setError('发送消息时出错，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };
  
  // 处理文件上传
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || isLoading) return;
    
    // 确定文件类型
    let fileType: 'pdf' | 'audio' | 'video';
    if (file.type === 'application/pdf') {
      fileType = 'pdf';
    } else if (file.type.startsWith('audio/')) {
      fileType = 'audio';
    } else if (file.type.startsWith('video/')) {
      fileType = 'video';
    } else {
      setError('不支持的文件类型');
      return;
    }
    
    // 添加上传消息
    const typeLabel = fileType === 'pdf' ? 'PDF文档' : 
                     fileType === 'audio' ? '音频文件' : '视频文件';
    
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: `上传了一个${typeLabel}: ${file.name}` },
    ]);
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await uploadFile(file, fileType);
      
      if (response.error) {
        setError(response.error);
      } else if (response.content) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: response.content },
        ]);
      }
    } catch (err) {
      setError('文件上传时出错，请稍后重试');
    } finally {
      setIsLoading(false);
      // 重置文件输入以允许上传相同文件
      e.target.value = '';
    }
  };
  
  return (
    <div className="flex flex-col h-full">
      {/* 消息历史区域 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 my-8">
            <p className="text-xl font-medium">欢迎使用AI学习助手</p>
            <p className="mt-2">您可以直接提问或上传文件进行分析</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-100 text-blue-900'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="font-medium mb-1">
                  {message.role === 'user' ? '你' : 'AI助手'}
                </div>
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            </div>
          ))
        )}
        
        {/* 加载指示器 */}
        {isLoading && (
          <div className="flex justify-center items-center py-2">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          </div>
        )}
        
        {/* 错误消息 */}
        {error && (
          <div className="bg-red-50 text-red-500 p-3 rounded-lg">
            <p className="font-medium">出错了</p>
            <p>{error}</p>
          </div>
        )}
      </div>
      
      {/* 输入区域 */}
      <Card className="mt-4 border-t p-4">
        <Tabs defaultValue="text" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="text">文字对话</TabsTrigger>
            <TabsTrigger value="file">文件上传</TabsTrigger>
          </TabsList>
          
          <TabsContent value="text" className="space-y-2">
            <Textarea
              placeholder="输入您的问题..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="min-h-[100px]"
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <Button 
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="w-full"
            >
              {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              发送
            </Button>
          </TabsContent>
          
          <TabsContent value="file">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={handleFileUpload}
                accept=".pdf,.mp3,.wav,.m4a,.mp4,.mov,.avi"
                disabled={isLoading}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer block"
              >
                <div className="flex flex-col items-center justify-center">
                  <div className="flex space-x-4 mb-4">
                    <FileText className="h-8 w-8 text-blue-500" />
                    <Music className="h-8 w-8 text-purple-500" />
                    <Video className="h-8 w-8 text-green-500" />
                  </div>
                  <p className="text-lg font-medium">点击或拖放文件到此处上传</p>
                  <p className="text-sm text-gray-500 mt-1">
                    支持PDF文档、音频文件(WAV,MP3,M4A)和视频文件(MP4,AVI,MOV)
                  </p>
                </div>
              </label>
            </div>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
} 