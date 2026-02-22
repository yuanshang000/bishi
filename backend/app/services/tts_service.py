"""
文本转语音服务

使用 edge-tts 将文本转换为音频
"""

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Optional
import os
import functools

logger = logging.getLogger(__name__)


class TTSService:
    """文本转语音服务类 (使用 pyttsx3 离线库)"""

    def __init__(self):
        """初始化TTS服务"""
        # 音频文件存储目录
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TTS Service initialized, audio directory: {self.audio_dir}")

    def _get_audio_filename(self, text: str) -> str:
        """
        根据文本内容生成唯一的音频文件名
        """
        # 使用MD5哈希生成唯一文件名
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        # pyttsx3 通常生成 wav 格式
        return f"listening_{text_hash}.wav"

    def _generate_audio_file(self, text: str, output_path: str):
        """
        使用 pyttsx3 同步生成音频文件
        """
        try:
            if pyttsx3 is None:
                raise RuntimeError("pyttsx3 is not installed")
            engine = pyttsx3.init()
            
            # 尝试设置英文语音
            voices = engine.getProperty('voices')
            english_voice = None
            for voice in voices:
                # 优先找包含 "English" 或 "en-US" 的语音
                if "english" in voice.name.lower() or "en-us" in voice.id.lower():
                    english_voice = voice.id
                    break
            
            if english_voice:
                engine.setProperty('voice', english_voice)
            
            # 设置语速 (默认通常较快，稍微调慢一点)
            engine.setProperty('rate', 150)
            
            engine.save_to_file(text, output_path)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 generation failed: {e}")
            raise

    async def _text_to_speech_async(self, text: str, output_path: Path) -> None:
        """
        异步将文本转换为语音（内部方法）
        """
        loop = asyncio.get_event_loop()
        # 在线程池中运行同步的 pyttsx3 代码，避免阻塞主循环
        await loop.run_in_executor(
            None, 
            functools.partial(self._generate_audio_file, text, str(output_path))
        )

        logger.info(f"Audio generated: {output_path}")

    async def text_to_speech(self, text: str) -> str:
        """
        将文本转换为语音文件

        Args:
            text: 要转换的文本

        Returns:
            str: 音频文件的相对URL路径
        """
        try:
            logger.info(f"=== TTS Service Called ===")
            logger.info(f"Input text length: {len(text)} chars")
            logger.debug(f"Input text preview: {text[:200]}...")

            # 生成文件名
            filename = self._get_audio_filename(text)
            output_path = self.audio_dir / filename

            logger.info(f"Generated filename: {filename}")
            logger.info(f"Output path: {output_path}")

            # 检查文件是否已存在（缓存）
            if output_path.exists():
                logger.info(f"Audio file already exists (cached): {filename}")
                return f"/static/audio/{filename}"

            # 执行异步转换
            logger.info(f"Starting audio generation...")
            await self._text_to_speech_async(text, output_path)

            # 验证文件是否成功创建
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"Audio file created successfully: {filename} ({file_size} bytes)")
            else:
                logger.error(f"Audio file was not created: {output_path}")
                raise Exception("Audio file generation failed - file not found after conversion")

            # 返回相对URL路径
            audio_url = f"/static/audio/{filename}"
            logger.info(f"Returning audio URL: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"Error converting text to speech: {e}", exc_info=True)
            raise

    def batch_text_to_speech(self, texts: list[str]) -> list[str]:
        """
        批量将文本转换为语音文件

        Args:
            texts: 文本列表

        Returns:
            list[str]: 音频文件URL列表
        """
        results = []
        for text in texts:
            try:
                audio_url = self.text_to_speech(text)
                results.append(audio_url)
            except Exception as e:
                logger.error(f"Error in batch conversion: {e}")
                results.append(None)

        return results

    def delete_audio(self, audio_url: str) -> bool:
        """
        删除音频文件

        Args:
            audio_url: 音频URL路径

        Returns:
            bool: 是否删除成功
        """
        try:
            # 从URL提取文件名
            filename = audio_url.split('/')[-1]
            file_path = self.audio_dir / filename

            if file_path.exists():
                os.remove(file_path)
                logger.info(f"Audio file deleted: {filename}")
                return True
            else:
                logger.warning(f"Audio file not found: {filename}")
                return False

        except Exception as e:
            logger.error(f"Error deleting audio file: {e}")
            return False


# 创建全局实例
tts_service = TTSService()
