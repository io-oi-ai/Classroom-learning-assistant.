import PyPDF2
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import os
from app.core.config import settings
from app.services.ai_service import get_ai_response

async def process_pdf(file_path: str) -> str:
    """处理PDF文件并提取文本内容"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # 使用AI处理提取的文本
        response = await get_ai_response(text)
        return response
    except Exception as e:
        raise Exception(f"PDF处理错误: {str(e)}")

async def process_audio(file_path: str) -> str:
    """处理音频文件并转换为文本"""
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='zh-CN')
        
        # 使用AI处理提取的文本
        response = await get_ai_response(text)
        return response
    except Exception as e:
        raise Exception(f"音频处理错误: {str(e)}")

async def process_video(file_path: str) -> str:
    """处理视频文件并提取音频内容"""
    try:
        # 从视频中提取音频
        video = VideoFileClip(file_path)
        audio = video.audio
        audio_path = file_path + ".wav"
        audio.write_audiofile(audio_path)
        
        # 处理提取的音频
        response = await process_audio(audio_path)
        
        # 清理临时文件
        os.remove(audio_path)
        video.close()
        
        return response
    except Exception as e:
        raise Exception(f"视频处理错误: {str(e)}") 