"use client"

import { DialogFooter } from "@/components/ui/dialog"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { useChat } from "@ai-sdk/react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  FileText,
  Send,
  Upload,
  MessageSquare,
  Clock,
  Search,
  PlusCircle,
  ChevronDown,
  Paperclip,
  ImageIcon,
  File,
  BookOpen,
  GraduationCap,
  X,
  Music,
  Video,
  Database,
  ArrowRight,
} from "lucide-react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { v4 as uuidv4 } from "uuid"
import { Progress } from "@/components/ui/progress"

export default function LearningAssistant() {
  const [subjects, setSubjects] = useState([
    {
      name: "自动控制原理",
      color: "blue",
      teacher: "李教授",
      chats: [
        "自动控制系统的稳定性分析",
        "PID控制器的参数调整方法",
        "频率响应分析与波特图",
        "状态空间表示法的优势",
        "根轨迹法设计控制系统",
      ],
    },
    {
      name: "数据结构",
      color: "green",
      teacher: "王教授",
      chats: [
        "二叉树的遍历算法比较",
        "红黑树与AVL树的区别",
        "图的最短路径算法",
        "哈希表的冲突解决策略",
        "排序算法的时间复杂度分析",
      ],
    },
    {
      name: "计算机网络",
      color: "purple",
      teacher: "张教授",
      chats: [
        "TCP/IP协议栈的层次结构",
        "HTTP与HTTPS的区别",
        "网络安全中的加密技术",
        "DNS解析过程详解",
        "IPv4向IPv6过渡的挑战",
      ],
    },
    {
      name: "高等数学",
      color: "yellow",
      teacher: "陈教授",
      chats: [
        "多元函数微分学应用",
        "级数收敛性判别方法",
        "拉普拉斯变换的性质",
        "傅里叶级数展开技巧",
        "偏微分方程求解方法",
      ],
    },
    {
      name: "机器学习",
      color: "red",
      teacher: "刘教授",
      chats: [
        "神经网络的反向传播算法",
        "支持向量机的核函数选择",
        "决策树与随机森林比较",
        "无监督学习中的聚类方法",
        "过拟合问题的解决方案",
      ],
    },
  ])
  const [activeSubject, setActiveSubject] = useState<number>(0)
  const { messages, input, handleInputChange, handleSubmit, isLoading, setMessages, setInput } = useChat({
    api: "/api/chat",
    initialMessages: [
      {
        id: "welcome-message",
        role: "assistant",
        content: `您好！我是${subjects[activeSubject]?.teacher}，${subjects[activeSubject]?.name}领域的专家。很高兴能帮助您解答问题。请问您想了解什么内容呢？`,
      },
    ],
    onResponse: (response) => {
      // 当收到响应时的回调
      console.log("收到AI响应:", response)
      // 确保滚动到最新消息
      setTimeout(() => {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
        }
      }, 100)
    },
    onError: (error) => {
      // 错误处理
      console.error("AI响应错误:", error)
      // 显示错误消息
      setMessages((messages) => [
        ...messages,
        {
          id: uuidv4(),
          role: "assistant",
          content: "抱歉，我遇到了一些问题。请稍后再试。",
        },
      ])
    },
  })

  const [files, setFiles] = useState<FileList | undefined>(undefined)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const knowledgeFileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [activeChat, setActiveChat] = useState<number>(0)
  const [isAddKnowledgeBaseOpen, setIsAddKnowledgeBaseOpen] = useState(false)
  const [isNewChatOpen, setIsNewChatOpen] = useState(false)
  const [newChatMessage, setNewChatMessage] = useState("")
  const [newSubject, setNewSubject] = useState({ name: "", teacher: "" })
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isKnowledgeUploadOpen, setIsKnowledgeUploadOpen] = useState(false)
  const [knowledgeFiles, setKnowledgeFiles] = useState<File[]>([])
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})
  const [isUploading, setIsUploading] = useState(false)

  const colors = ["blue", "green", "purple", "yellow", "red", "pink", "indigo", "orange", "teal"]

  // 滚动到最新消息
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(e.dataTransfer.files)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(e.target.files)
    }
  }

  const handleKnowledgeFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      setKnowledgeFiles((prev) => [...prev, ...newFiles])

      // 初始化上传进度
      const newProgress = { ...uploadProgress }
      newFiles.forEach((file) => {
        newProgress[file.name] = 0
      })
      setUploadProgress(newProgress)
    }
  }

  const handleKnowledgeFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files)
      setKnowledgeFiles((prev) => [...prev, ...newFiles])

      // 初始化上传进度
      const newProgress = { ...uploadProgress }
      newFiles.forEach((file) => {
        newProgress[file.name] = 0
      })
      setUploadProgress(newProgress)
    }
  }

  const removeKnowledgeFile = (fileName: string) => {
    setKnowledgeFiles((prev) => prev.filter((file) => file.name !== fileName))

    // 移除进度记录
    const newProgress = { ...uploadProgress }
    delete newProgress[fileName]
    setUploadProgress(newProgress)
  }

  const uploadKnowledgeFiles = async () => {
    if (knowledgeFiles.length === 0) return

    setIsUploading(true)

    // 模拟上传过程
    for (const file of knowledgeFiles) {
      // 模拟分块上传
      for (let progress = 0; progress <= 100; progress += 5) {
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: progress,
        }))
        await new Promise((resolve) => setTimeout(resolve, 100)) // 模拟网络延迟
      }

      // 模拟AI处理文件
      await new Promise((resolve) => setTimeout(resolve, 500))
    }

    // 上传完成后，添加一条AI消息
    setMessages((prev) => [
      ...prev,
      {
        id: uuidv4(),
        role: "assistant",
        content: `我已经学习了您上传的${knowledgeFiles.length}个文件，并将其添加到我的知识库中。现在您可以向我提问相关内容了！`,
      },
    ])

    // 清空文件列表和进度
    setKnowledgeFiles([])
    setUploadProgress({})
    setIsUploading(false)
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split(".").pop()?.toLowerCase()

    if (["pdf"].includes(extension || "")) {
      return <File className="h-5 w-5 text-red-500" />
    } else if (["jpg", "jpeg", "png", "gif", "webp"].includes(extension || "")) {
      return <ImageIcon className="h-5 w-5 text-blue-500" />
    } else if (["mp3", "wav", "ogg"].includes(extension || "")) {
      return <Music className="h-5 w-5 text-purple-500" />
    } else if (["mp4", "webm", "avi", "mov"].includes(extension || "")) {
      return <Video className="h-5 w-5 text-green-500" />
    } else {
      return <FileText className="h-5 w-5 text-gray-500" />
    }
  }

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    // 如果没有输入内容且没有文件，则不提交
    if (!input.trim() && (!files || files.length === 0)) {
      return
    }

    // 如果有输入内容，将其添加到当前学科的聊天记录中
    if (input.trim()) {
      const updatedSubjects = [...subjects]
      // 如果是新对话，添加到开头；如果是已有对话，更新标题
      if (messages.length === 0) {
        updatedSubjects[activeSubject].chats.unshift(input.trim())
      } else if (activeChat === 0) {
        // 如果是当前对话的第一条消息，更新标题
        updatedSubjects[activeSubject].chats[activeChat] = input.trim()
      }
      setSubjects(updatedSubjects)
    }

    // 提交表单，发送消息给AI
    handleSubmit(e, {
      experimental_attachments: files,
    })

    // 清空文件
    setFiles(undefined)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }

    // 确保滚动到最新消息
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
      }
    }, 100)
  }

  const handleAddKnowledgeBase = () => {
    if (newSubject.name.trim() && newSubject.teacher.trim()) {
      // 随机选择一个颜色
      const randomColor = colors[Math.floor(Math.random() * colors.length)]

      // 添加新的知识库
      const newSubjectItem = {
        name: newSubject.name,
        teacher: newSubject.teacher,
        color: randomColor,
        chats: [], // 新知识库初始没有聊天记录
      }

      setSubjects([...subjects, newSubjectItem])

      // 重置表单并关闭对话框
      setNewSubject({ name: "", teacher: "" })
      setIsAddKnowledgeBaseOpen(false)

      // 自动切换到新添加的知识库
      setActiveSubject(subjects.length)
      setActiveChat(0) // 重置活跃聊天索引
    }
  }

  const handleStartNewChat = async () => {
    if (newChatMessage.trim()) {
      // 添加新的对话到当前学科的聊天记录中
      const updatedSubjects = [...subjects]
      updatedSubjects[activeSubject].chats.unshift(newChatMessage.trim())
      setSubjects(updatedSubjects)

      // 关闭对话框
      setIsNewChatOpen(false)

      // 重置聊天界面，但保留欢迎消息
      const welcomeMessage = {
        id: "welcome-message",
        role: "assistant",
        content: `您好！我是${subjects[activeSubject]?.teacher}，${subjects[activeSubject]?.name}领域的专家。很高兴能帮助您解答问题。`,
      }

      // 创建用户消息对象
      const userMessage = {
        id: uuidv4(),
        role: "user",
        content: newChatMessage.trim(),
      }

      // 将欢迎消息和用户消息添加到聊天界面
      setMessages([welcomeMessage, userMessage])

      // 设置活跃聊天为新创建的聊天
      setActiveChat(0)

      // 直接调用API发送消息给AI
      try {
        // 显示加载状态
        const loadingId = uuidv4()
        setMessages((prev) => [...prev, { id: loadingId, role: "assistant", content: "正在思考...", isLoading: true }])

        // 发送API请求
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            messages: [
              {
                role: "system",
                content: `你是一位${subjects[activeSubject]?.name}领域的专家${subjects[activeSubject]?.teacher}。请用专业且易懂的方式回答问题。`,
              },
              {
                role: "user",
                content: newChatMessage.trim(),
              },
            ],
          }),
        })

        if (!response.ok) {
          throw new Error("AI响应出错")
        }

        const data = await response.json()

        // 移除加载消息，添加AI回复
        setMessages((prev) =>
          prev
            .filter((msg) => msg.id !== loadingId)
            .concat({
              id: uuidv4(),
              role: "assistant",
              content: data.text || "抱歉，我无法理解您的问题。请尝试重新表述。",
            }),
        )

        // 清空输入框和新对话消息
        setInput("")
        setNewChatMessage("")

        // 确保滚动到最新消息
        setTimeout(() => {
          if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
          }
        }, 100)
      } catch (error) {
        console.error("发送消息失败:", error)
        // 显示错误消息
        setMessages((prev) =>
          prev
            .filter((msg) => !msg.isLoading)
            .concat({
              id: uuidv4(),
              role: "assistant",
              content: "抱歉，我遇到了一些问题。请稍后再试。",
            }),
        )
      }
    }
  }

  useEffect(() => {
    // 当切换学科时，重置活跃聊天索引
    setActiveChat(0)

    // 当切换学科时，可以加载对应老师的信息和相关内容
    console.log(`切换到学科: ${subjects[activeSubject].name}, 老师: ${subjects[activeSubject].teacher}`)
    // 在实际应用中，您可能需要从API获取老师信息和相关课程内容
  }, [activeSubject])

  // 获取当前学科的聊天记录
  const currentSubjectChats = subjects[activeSubject].chats || []

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 border-r bg-white flex flex-col">
        <div className="p-4 flex items-center gap-2 border-b">
          <div className="h-8 w-8 rounded-full bg-purple-600 flex items-center justify-center">
            <span className="text-white font-bold">AI</span>
          </div>
          <span className="font-semibold">学习助手</span>
        </div>

        <div className="p-3">
          <Button variant="outline" className="w-full justify-start gap-2 mb-4" onClick={() => setIsNewChatOpen(true)}>
            <PlusCircle className="h-4 w-4" />
            <span>新对话</span>
          </Button>
        </div>

        <div className="flex items-center px-4 py-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <FileText className="h-4 w-4" />
            <span>知识库</span>
          </div>
          <Button variant="ghost" size="icon" className="ml-auto" onClick={() => setIsAddKnowledgeBaseOpen(true)}>
            <PlusCircle className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="max-h-32 overflow-y-auto">
          {subjects.map((subject, index) => (
            <div
              key={index}
              className={`px-4 py-2 text-sm hover:bg-gray-100 cursor-pointer flex items-center gap-2 ${activeSubject === index ? "bg-blue-50 border-l-2 border-blue-500" : ""}`}
              onClick={() => setActiveSubject(index)}
            >
              <div className={`w-2 h-2 rounded-full bg-${subject.color}-500`}></div>
              <span>{subject.name}</span>
            </div>
          ))}
        </ScrollArea>

        <div className="flex items-center px-4 py-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Clock className="h-4 w-4" />
            <span>最近对话</span>
          </div>
          <Button variant="ghost" size="icon" className="ml-auto">
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="flex-1">
          {currentSubjectChats.length > 0 ? (
            currentSubjectChats.map((chat, index) => (
              <div
                key={index}
                className={`px-4 py-2 text-sm hover:bg-gray-100 cursor-pointer ${activeChat === index ? "bg-blue-50 border-l-2 border-blue-500" : ""} whitespace-nowrap overflow-hidden text-ellipsis`}
                onClick={() => setActiveChat(index)}
              >
                {chat}
              </div>
            ))
          ) : (
            <div className="px-4 py-6 text-center text-sm text-gray-500">暂无对话记录</div>
          )}
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b bg-white flex justify-between items-center">
          <Tabs defaultValue="chat">
            <TabsList>
              <TabsTrigger value="chat">聊天</TabsTrigger>
              <TabsTrigger value="search">搜索</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-blue-500" />
            <span className="font-medium">
              {subjects[activeSubject]?.teacher} - {subjects[activeSubject]?.name}
            </span>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4 relative">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mb-4">
                <MessageSquare className="h-8 w-8 text-blue-500" />
              </div>
              <h2 className="text-2xl font-bold mb-2">我是{subjects[activeSubject]?.teacher}的学习助手</h2>
              <p className="text-gray-500 mb-6">
                专注于{subjects[activeSubject]?.name}领域，上传文件并提问，我将帮助你理解内容
              </p>

              <div className="grid grid-cols-4 gap-4 max-w-2xl">
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <FileText className="h-6 w-6 mb-2" />
                  <span className="text-xs">文档分析</span>
                </Button>
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <Search className="h-6 w-6 mb-2" />
                  <span className="text-xs">AI搜索</span>
                </Button>
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <BookOpen className="h-6 w-6 mb-2" />
                  <span className="text-xs">课程资料</span>
                </Button>
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <ImageIcon className="h-6 w-6 mb-2" />
                  <span className="text-xs">图像生成</span>
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 添加一个示例AI回复，确保界面显示正确 */}
              {messages.length === 1 && messages[0].role === "user" && (
                <div className="flex justify-start">
                  <div className="flex gap-3 max-w-3xl">
                    <Avatar>
                      <AvatarFallback>{subjects[activeSubject]?.teacher.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <Card>
                      <CardContent className="p-4">
                        <div className="whitespace-pre-wrap">
                          您好！我是{subjects[activeSubject]?.teacher}，{subjects[activeSubject]?.name}
                          领域的专家。很高兴能帮助您解答问题。请问您想了解什么内容呢？
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* 显示所有消息 */}
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`flex gap-3 max-w-3xl ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                    <Avatar>
                      <AvatarFallback>
                        {message.role === "user" ? "用户" : subjects[activeSubject]?.teacher.charAt(0)}
                      </AvatarFallback>
                    </Avatar>
                    <Card className={message.role === "assistant" ? "bg-blue-50" : ""}>
                      <CardContent className="p-4">
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        {message.experimental_attachments?.map((attachment, index) => (
                          <div key={index} className="mt-2">
                            {attachment.contentType?.startsWith("image/") ? (
                              <img
                                src={attachment.url || "/placeholder.svg"}
                                alt={attachment.name || `Attachment ${index}`}
                                className="max-w-full rounded-md border"
                              />
                            ) : attachment.contentType?.startsWith("application/pdf") ? (
                              <div className="flex items-center gap-2 p-2 border rounded-md bg-gray-50">
                                <File className="h-5 w-5 text-red-500" />
                                <span>{attachment.name || `PDF ${index}`}</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 p-2 border rounded-md bg-gray-50">
                                <FileText className="h-5 w-5" />
                                <span>{attachment.name || `File ${index}`}</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              ))}

              {/* 显示AI正在输入的状态 */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex gap-3 max-w-3xl">
                    <Avatar>
                      <AvatarFallback>{subjects[activeSubject]?.teacher.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          ></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.4s" }}
                          ></div>
                          <span className="text-sm text-gray-500 ml-1">正在思考...</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              {/* 用于自动滚动到最新消息的引用元素 */}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* 固定在ScrollArea右下角的文件上传窗口 */}
          <div className={`absolute bottom-4 right-4 z-50 ${isKnowledgeUploadOpen ? "w-80" : "w-14"}`}>
            <Card className="shadow-lg border-blue-200 transition-all duration-300">
              <CardHeader
                className={`p-3 bg-blue-500 text-white rounded-t-lg flex ${isKnowledgeUploadOpen ? "justify-between" : "justify-center"} items-center cursor-pointer`}
                onClick={() => setIsKnowledgeUploadOpen(!isKnowledgeUploadOpen)}
              >
                {isKnowledgeUploadOpen ? (
                  <>
                    <CardTitle className="text-sm flex items-center">
                      <Database className="h-4 w-4 mr-2" />
                      添加到知识库
                    </CardTitle>
                    <X className="h-4 w-4 cursor-pointer" />
                  </>
                ) : (
                  <Database className="h-6 w-6" />
                )}
              </CardHeader>

              {isKnowledgeUploadOpen && (
                <>
                  <CardContent className="p-3 space-y-3">
                    <div
                      className="border-2 border-dashed border-blue-300 rounded-md p-4 text-center cursor-pointer hover:bg-blue-50 transition-colors"
                      onClick={() => knowledgeFileInputRef.current?.click()}
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={handleKnowledgeFileDrop}
                    >
                      <Upload className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                      <p className="text-sm text-blue-700">点击或拖放文件到这里</p>
                      <p className="text-xs text-gray-500 mt-1">支持PDF、音频、视频等格式</p>
                      <input
                        type="file"
                        ref={knowledgeFileInputRef}
                        onChange={handleKnowledgeFileChange}
                        className="hidden"
                        multiple
                        accept=".pdf,.doc,.docx,.txt,.mp3,.wav,.mp4,.avi,.jpg,.jpeg,.png"
                      />
                    </div>

                    {knowledgeFiles.length > 0 && (
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {knowledgeFiles.map((file, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded-md">
                            <div className="flex items-center gap-2 text-sm overflow-hidden">
                              {getFileIcon(file.name)}
                              <span className="truncate">{file.name}</span>
                            </div>
                            <div className="flex items-center">
                              {uploadProgress[file.name] > 0 && uploadProgress[file.name] < 100 ? (
                                <div className="w-16">
                                  <Progress value={uploadProgress[file.name]} className="h-1" />
                                </div>
                              ) : uploadProgress[file.name] === 100 ? (
                                <div className="text-green-500 text-xs">完成</div>
                              ) : (
                                <X
                                  className="h-4 w-4 text-gray-500 hover:text-red-500 cursor-pointer"
                                  onClick={() => removeKnowledgeFile(file.name)}
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>

                  <CardFooter className="p-3 pt-0">
                    <Button
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center gap-2"
                      onClick={uploadKnowledgeFiles}
                      disabled={knowledgeFiles.length === 0 || isUploading}
                    >
                      {isUploading ? (
                        <div className="flex items-center">
                          <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                          处理中...
                        </div>
                      ) : (
                        <>
                          <ArrowRight className="h-4 w-4" />
                          <span>上传到知识库</span>
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </>
              )}
            </Card>
          </div>
        </ScrollArea>

        {/* Message Input Area */}
        <div className="p-4 border-t bg-white">
          <form onSubmit={handleFormSubmit} className="relative">
            <Textarea
              value={input}
              onChange={handleInputChange}
              placeholder={`向${subjects[activeSubject]?.teacher}提问关于${subjects[activeSubject]?.name}的问题...`}
              className="min-h-[80px] pr-24 resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  const form = e.currentTarget.form
                  if (form) form.requestSubmit()
                }
              }}
              disabled={isLoading}
            />

            <div className="absolute bottom-3 right-3 flex items-center gap-2">
              <div
                className={`relative p-2 rounded-md cursor-pointer ${isDragging ? "bg-blue-100" : "hover:bg-gray-100"} ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isLoading && fileInputRef.current?.click()}
              >
                <Paperclip className="h-5 w-5 text-gray-500" />
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                  multiple
                  disabled={isLoading}
                />
                {files && files.length > 0 && (
                  <div className="absolute -top-1 -right-1 bg-blue-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-xs">
                    {files.length}
                  </div>
                )}
              </div>

              <Button type="submit" size="icon" disabled={isLoading || (!input && (!files || files.length === 0))}>
                {isLoading ? (
                  <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>

            {/* File Upload Area */}
            {isDragging && !isLoading && (
              <div className="absolute inset-0 bg-blue-50 bg-opacity-90 border-2 border-dashed border-blue-300 rounded-md flex items-center justify-center">
                <div className="text-center">
                  <Upload className="h-10 w-10 text-blue-500 mx-auto mb-2" />
                  <p className="text-blue-700">拖放文件到这里上传</p>
                </div>
              </div>
            )}

            {/* File Preview */}
            {files && files.length > 0 && (
              <div className="mt-2 p-2 bg-gray-50 rounded-md">
                <div className="text-sm font-medium mb-1">已选择的文件：</div>
                <div className="space-y-1">
                  {Array.from(files).map((file, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <FileText className="h-4 w-4" />
                      <span>{file.name}</span>
                      <span className="text-gray-500 text-xs">({(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </form>
        </div>
      </div>

      {/* 添加知识库对话框 */}
      <Dialog open={isAddKnowledgeBaseOpen} onOpenChange={setIsAddKnowledgeBaseOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>添加新知识库</DialogTitle>
            <DialogDescription>添加一个新的学科知识库和对应的老师。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="subject-name" className="text-right">
                学科名称
              </Label>
              <Input
                id="subject-name"
                value={newSubject.name}
                onChange={(e) => setNewSubject({ ...newSubject, name: e.target.value })}
                className="col-span-3"
                placeholder="例如：人工智能"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="teacher-name" className="text-right">
                老师姓名
              </Label>
              <Input
                id="teacher-name"
                value={newSubject.teacher}
                onChange={(e) => setNewSubject({ ...newSubject, teacher: e.target.value })}
                className="col-span-3"
                placeholder="例如：赵教授"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddKnowledgeBaseOpen(false)}>
              取消
            </Button>
            <Button onClick={handleAddKnowledgeBase} disabled={!newSubject.name || !newSubject.teacher}>
              添加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 新对话对话框 */}
      <Dialog open={isNewChatOpen} onOpenChange={setIsNewChatOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>开始新对话</DialogTitle>
            <DialogDescription>输入您的问题，开始一个新的对话。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="chat-message" className="text-right">
                问题
              </Label>
              <Textarea
                id="chat-message"
                value={newChatMessage}
                onChange={(e) => setNewChatMessage(e.target.value)}
                className="col-span-3 min-h-[100px]"
                placeholder={`向${subjects[activeSubject]?.teacher}提问关于${subjects[activeSubject]?.name}的问题...`}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewChatOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleStartNewChat}
              disabled={!newChatMessage.trim() || isLoading}
              className="relative bg-blue-600 hover:bg-blue-700 text-white"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  处理中...
                </div>
              ) : (
                "开始对话"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

