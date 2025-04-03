import ChatInterface from "@/components/chat/ChatInterface";

export default function Home() {
  return (
    <main className="container max-w-4xl mx-auto py-6 px-4">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">AI学习助手</h1>
        <p className="text-gray-500 mt-2">
          支持文本对话、PDF文档、音频和视频分析
        </p>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border min-h-[70vh] flex flex-col">
        <ChatInterface />
      </div>
    </main>
  );
} 