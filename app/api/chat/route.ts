import { openai } from "@ai-sdk/openai"
import { streamText } from "ai"

// 允许流式响应最多30秒
export const maxDuration = 30

export async function POST(req: Request) {
  try {
    const { messages } = await req.json()

    // 使用OpenAI模型
    const result = streamText({
      model: openai("gpt-4o"),
      messages,
    })

    return result.toDataStreamResponse()
  } catch (error) {
    console.error("Chat API error:", error)
    return new Response(JSON.stringify({ error: "Failed to process your request" }), {
      status: 500,
      headers: {
        "Content-Type": "application/json",
      },
    })
  }
}

