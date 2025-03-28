from google.cloud import aiplatform
from app.core.config import settings
import json

async def get_ai_response(text: str) -> str:
    """使用Google AI Studio API处理文本并返回响应"""
    try:
        # 初始化AI平台
        aiplatform.init(project="your-project-id", location="us-central1")
        
        # 创建模型实例
        model = aiplatform.TextGenerationModel.from_pretrained("text-bison@001")
        
        # 构建提示词
        prompt = f"""
        请分析以下内容并给出专业的回复：
        
        {text}
        
        请用中文回复，并保持专业、准确和友好的语气。
        """
        
        # 调用模型
        response = model.predict(prompt)
        
        return response.text
    except Exception as e:
        raise Exception(f"AI处理错误: {str(e)}") 