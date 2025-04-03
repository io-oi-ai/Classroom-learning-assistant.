"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";

interface Message {
  sender: "user" | "ai";
  content: string;
}

export default function ChatInterface() {
  const [activeTab, setActiveTab] = useState("text");
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  
  // 发送文本消息
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    setError("");
    setIsLoading(true);
    
    // 添加用户消息到聊天历史
    const userMessage: Message = { sender: "user", content: inputMessage };
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: inputMessage }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // 添加AI回复到聊天历史
        const aiMessage: Message = { sender: "ai", content: data.response };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        setError(data.error || "发送消息失败");
      }
    } catch (error) {
      setError("发送消息失败：" + error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 处理文件上传
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    setError("");
    setIsLoading(true);
    
    // 确定文件类型
    let fileType = "";
    if (file.type === "application/pdf") {
      fileType = "pdf";
    } else if (file.type.startsWith("audio/")) {
      fileType = "audio";
    } else if (file.type.startsWith("video/")) {
      fileType = "video";
    } else {
      setError("不支持的文件类型");
      setIsLoading(false);
      return;
    }
    
    // 添加用户上传消息到聊天历史
    const userMessage: Message = { 
      sender: "user", 
      content: `上传了一个${
        fileType === "pdf" ? "PDF文档" : 
        fileType === "audio" ? "音频文件" : 
        "视频文件"
      }: ${file.name}` 
    };
    setMessages((prev) => [...prev, userMessage]);
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await fetch(`/api/upload/${fileType}`, {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // 添加AI回复到聊天历史
        const aiMessage: Message = { sender: "ai", content: data.content };
        setMessages((prev) => [...prev, aiMessage]);
      } else {
        setError(data.error || "上传文件失败");
      }
    } catch (error) {
      setError("上传文件失败：" + error.message);
    } finally {
      setIsLoading(false);
      // 清空文件输入框，允许再次上传相同文件
      event.target.value = "";
    }
  };
  
  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="text-center text-2xl">AI学习助手</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="text" onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="text">文字对话</TabsTrigger>
              <TabsTrigger value="upload">文件上传</TabsTrigger>
            </TabsList>
            
            <TabsContent value="text" className="space-y-4">
              <div className="flex flex-col">
                <Textarea
                  placeholder="输入您的问题..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  className="min-h-[120px] mb-2"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                />
                <Button 
                  onClick={handleSendMessage} 
                  disabled={isLoading || !inputMessage.trim()}
                >
                  {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  发送
                </Button>
              </div>
            </TabsContent>
            
            <TabsContent value="upload" className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:bg-gray-50 transition-colors">
                <Label htmlFor="file-upload" className="cursor-pointer">
                  <div className="space-y-2">
                    <div className="text-lg">点击或拖放文件到此处上传</div>
                    <div className="text-sm text-gray-500">
                      支持的文件类型: PDF文档, 音频文件(WAV,MP3,M4A), 视频文件(MP4,AVI,MOV)
                    </div>
                  </div>
                  <Input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.wav,.mp3,.m4a,.mp4,.avi,.mov"
                    onChange={handleFileUpload}
                  />
                </Label>
              </div>
            </TabsContent>
          </Tabs>
          
          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-600 rounded-md">
              {error}
            </div>
          )}
          
          {isLoading && activeTab === "upload" && (
            <div className="mt-4 p-3 bg-blue-50 text-blue-600 rounded-md flex items-center">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              正在处理您的文件，请稍候...
            </div>
          )}
          
          {messages.length > 0 && (
            <div className="mt-8 space-y-4">
              <h3 className="text-lg font-medium">对话历史</h3>
              <div className="space-y-4">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      msg.sender === "user"
                        ? "bg-blue-50 ml-12"
                        : "bg-gray-50 mr-12"
                    }`}
                  >
                    <div className="font-semibold mb-1">
                      {msg.sender === "user" ? "你" : "AI助手"}
                    </div>
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
} 