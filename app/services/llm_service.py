import json
from typing import List, Dict, Any, Optional
from http import HTTPStatus
from app.core.config import get_settings
import requests

try:
    import dashscope
    from dashscope.audio.asr import Transcription
    DASHSCOPE_AVAILABLE = True
except ImportError as e:
    DASHSCOPE_AVAILABLE = False
    print(f"Warning: dashscope module not found. Using mock LLM service. Error: {e}")
    # Dummy classes
    class Transcription:
        @staticmethod
        def async_call(*args, **kwargs):
            return None
        @staticmethod
        def wait(*args, **kwargs):
            return None

settings = get_settings()
if DASHSCOPE_AVAILABLE:
    dashscope.api_key = settings.DASHSCOPE_API_KEY

class LLMService:
    def __init__(self):
        pass

    def _extract_transcription_text(self, data: Dict[str, Any]) -> str:
        text_parts = []
        for transcript in data.get("transcripts", []):
            transcript_text = str(transcript.get("text", "")).strip()
            if transcript_text:
                text_parts.append(transcript_text)
                continue
            for sentence in transcript.get("sentences", []):
                sentence_text = str(sentence.get("text", "")).strip()
                if sentence_text:
                    text_parts.append(sentence_text)
        return "\n".join(text_parts).strip()

    def transcribe_audio(self, file_url: str) -> str:
        """
        Transcribe audio from a URL using Qwen/DashScope ASR.
        """
        if not DASHSCOPE_AVAILABLE:
            print("Mocking transcription...")
            return "这是一个模拟的语音转录文本。用户说：我有一个关于人工智能的新想法，想要做一个能够自动记录和整理笔记的工具。"

        # Using dashscope.audio.asr.Transcription
        print(f"DEBUG: Transcribing URL: {file_url}")
        
        # Determine protocol
        if not file_url.startswith("http"):
             # Local file path? ASR needs URL or uploaded file
             # For now, if it's a local path, we might need to upload it to OSS or serve it via HTTP
             # Since we are using local storage mounted at /static, we can convert path to URL
             if "static/uploads" in file_url:
                 filename = file_url.split("/")[-1]
                 # Assuming localhost:8000
                 file_url = f"http://localhost:8000/static/uploads/{filename}"
                 print(f"DEBUG: Converted local path to URL: {file_url}")

        try:
            candidate_models = [settings.QWEN_ASR_MODEL]
            if settings.QWEN_ASR_MODEL != "paraformer-v2":
                candidate_models.append("paraformer-v2")

            task_response = None
            start_error = None
            for model_name in candidate_models:
                task_response = Transcription.async_call(
                    model=model_name,
                    file_urls=[file_url],
                    language_hints=['zh', 'en']
                )
                print(f"DEBUG: ASR Task Response ({model_name}): {task_response}")
                if task_response.status_code == HTTPStatus.OK:
                    break
                code = str(getattr(task_response, "code", ""))
                message = str(getattr(task_response, "message", ""))
                if code == "InvalidParameter" and "url error" in message.lower():
                    start_error = f"ASR Task Start Failed: {code} - {message}"
                    continue
                raise Exception(f"ASR Task Start Failed: {code} - {message}")

            if task_response is None or task_response.status_code != HTTPStatus.OK:
                raise Exception(start_error or "ASR Task Start Failed")
            
            transcription_response = Transcription.wait(task=task_response.output.task_id)
            
            if transcription_response.status_code == HTTPStatus.OK:
                # Check for results
                if 'results' in transcription_response.output and transcription_response.output['results']:
                     results = transcription_response.output['results']
                     text = ""
                     
                     for result in results:
                         # Check for transcription_url (Paraformer)
                         if 'transcription_url' in result and result['transcription_url']:
                             try:
                                 print(f"DEBUG: Downloading transcription from {result['transcription_url']}")
                                 resp = requests.get(result['transcription_url'])
                                 if resp.status_code == 200:
                                     data = resp.json()
                                     text += self._extract_transcription_text(data)
                             except Exception as e:
                                 print(f"Error downloading transcription: {e}")
                                 
                         # Check for sentences (Qwen/Older models)
                         elif 'sentences' in result:
                             for sentence in result['sentences']:
                                 text += sentence['text']
                                  
                     text = text.strip()
                     if not text:
                         raise Exception("ASR returned no transcript text")
                     return text
                else:
                     raise Exception("ASR returned no transcription results")
            else:
                raise Exception(f"ASR Failed: {transcription_response.code} - {transcription_response.message}")
        except Exception as e:
            print(f"ASR Exception: {e}")
            raise e

    def structure_note(self, raw_text: str) -> Dict[str, Any]:
        """
        Structure the raw text into a note format using Qwen-Plus.
        Returns a dictionary with keys: title, summary, core_ideas, key_features, possible_applications, tags
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                "title": "模拟笔记标题",
                "summary": "这是一个模拟的笔记摘要，用于测试环境。",
                "core_ideas": ["核心观点1", "核心观点2"],
                "key_features": ["功能1", "功能2"],
                "possible_applications": ["应用场景1", "应用场景2"],
                "tags": ["模拟", "测试", "AI"]
            }

        prompt = f"""
        你是一个专业的个人知识助理。请将以下用户的语音转录文本整理成结构化的笔记。
        
        原始文本:
        {raw_text}
        
        请输出 JSON 格式，包含以下字段:
        - title: 一个简短的标题 (String)
        - summary: 一句话摘要 (String)
        - core_ideas: 核心观点或想法列表 (List[String])
        - key_features: 关键功能或特性列表 (List[String])
        - possible_applications: 可能的应用场景列表 (List[String])
        - tags: 3-5个相关标签 (List[String])
        
        只返回 JSON 字符串，不要包含 Markdown 代码块标记。
        """
        
        try:
            response = dashscope.Generation.call(
                model=settings.QWEN_CHAT_MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                result_format='message',  # set the result to be "message" format.
            )
        except Exception as e:
            print(f"LLM Call Exception: {e}")
            raise e

        if response.status_code == HTTPStatus.OK:
            content = response.output.choices[0].message.content
            # Clean up potential markdown code blocks
            content = content.replace("```json", "").replace("```", "").strip()
            # Find the first { and last } to extract JSON
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                content = content[start_idx:end_idx+1]
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}, Raw content: {content}")
                # Fallback if JSON is invalid
                return {
                    "title": "未命名笔记",
                    "summary": "解析失败",
                    "core_ideas": [],
                    "key_features": [],
                    "possible_applications": [],
                    "tags": ["解析错误"]
                }
        else:
             raise Exception(f"LLM Chat Failed: {response.code} - {response.message}")

    def expand_idea(self, note_content: str) -> Dict[str, Any]:
        """
        Expand an idea into Product Form, Business Model, and Tech Implementation.
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                "features": ["扩展功能1", "扩展功能2"],
                "product_form": "模拟产品形态",
                "business_model": "模拟商业模式",
                "tech_implementation": "模拟技术方案"
            }

        prompt = f"""
        你是一个资深的产品经理和创业导师。用户提出一个想法，请帮助扩展。
        
        用户想法:
        {note_content}
        
        请输出 JSON 格式，包含以下字段:
        - features: 可能的功能列表 (List[String]) - 对应"功能"
        - product_form: 产品形态描述 (String) - 对应"产品形态"
        - business_model: 商业模式建议 (String) - 对应"商业模式"
        - tech_implementation: 技术实现方案 (String) - 对应"技术实现"
        
        只返回 JSON 字符串。
        """
        
        response = dashscope.Generation.call(
            model=settings.QWEN_CHAT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
        )
        
        return self._parse_json_response(response)

    def generate_roadmap(self, note_content: str) -> Dict[str, Any]:
        """
        Generate a 3-phase product roadmap.
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                "roadmap": [
                    {"phase": "第一阶段", "tasks": ["任务1", "任务2"]},
                    {"phase": "第二阶段", "tasks": ["任务3", "任务4"]},
                    {"phase": "第三阶段", "tasks": ["任务5", "任务6"]}
                ]
            }

        prompt = f"""
        你是一个项目经理。请为以下产品想法制定一个分阶段的实施路线图。
        
        产品想法:
        {note_content}
        
        请输出 JSON 格式，包含以下字段:
        - roadmap: 一个列表，每个元素包含:
            - phase: 阶段名称 (String, 如 "第一阶段：MVP验证")
            - tasks: 该阶段的关键任务列表 (List[String])
        
        只返回 JSON 字符串。
        """
        
        response = dashscope.Generation.call(
            model=settings.QWEN_CHAT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
        )
        
        return self._parse_json_response(response)

    def score_idea(self, note_content: str) -> Dict[str, Any]:
        """
        Score the idea on Innovation, Business Value, Tech Difficulty, Feasibility.
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                "innovation": 4,
                "business_value": 5,
                "tech_difficulty": 3,
                "feasibility": 4,
                "reason": "模拟评分：想法不错，值得尝试。"
            }

        prompt = f"""
        你是一个风险投资人和技术专家。请对以下想法进行多维度评分（1-5星）。
        
        用户想法:
        {note_content}
        
        请输出 JSON 格式，包含以下字段:
        - innovation: 创新性 (Int, 1-5)
        - business_value: 商业价值 (Int, 1-5)
        - tech_difficulty: 技术难度 (Int, 1-5, 分数越高越难)
        - feasibility: 落地可行性 (Int, 1-5)
        - reason: 简短的评分理由 (String, 100字以内，仅解释评分依据，不要包含后续建议或路线图清单)
        
        只返回 JSON 字符串。
        """
        
        response = dashscope.Generation.call(
            model=settings.QWEN_CHAT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
        )
        
        return self._parse_json_response(response)

    def chat_with_notes(self, query: str, context_notes: List[Dict[str, Any]]) -> str:
        """
        Chat with knowledge base context.
        """
        if not DASHSCOPE_AVAILABLE:
            return f"模拟回答：针对你的问题 '{query}'，结合上下文，我认为..."

        # Prepare context string
        context_str = ""
        for i, note in enumerate(context_notes):
            meta = note.get('metadata', {})
            context_str += f"[{i+1}] {meta.get('title', '无标题')}: {meta.get('summary', '')}\n"
            
        prompt = f"""
        你是一个个人知识库助手。请根据以下参考笔记回答用户的问题。
        如果问题与笔记无关，请直接回答。
        
        参考笔记:
        {context_str}
        
        用户问题: {query}
        """
        
        response = dashscope.Generation.call(
            model=settings.QWEN_CHAT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        else:
            return "抱歉，我现在无法回答。"

    def generate_weekly_summary(self, notes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a weekly summary from a list of notes.
        """
        if not DASHSCOPE_AVAILABLE:
            return {
                "total_count": len(notes),
                "topic_breakdown": [{"topic": "模拟主题", "count": len(notes)}],
                "key_highlights": ["模拟高光时刻1", "模拟高光时刻2"],
                "weekly_synthesis": "本周模拟总结：非常充实。"
            }

        if not notes:
            return {
                "total_count": 0,
                "summary_markdown": "本周没有记录任何想法。"
            }
            
        notes_text = ""
        for i, note in enumerate(notes):
            meta = note.get('metadata', {})
            created_at = meta.get('created_at_str', '未知时间')
            notes_text += f"{i+1}. [{created_at}] {meta.get('title', '无标题')}\n   摘要: {meta.get('summary', '')}\n   标签: {meta.get('tags', '')}\n\n"
            
        prompt = f"""
        你是一个高效的个人知识助理。请根据以下用户本周记录的想法，生成一份精简的周报总结。
        
        用户本周想法列表:
        {notes_text}
        
        请输出 JSON 格式，包含以下字段:
        - total_count: 本周记录总数 (Int)
        - topic_breakdown: 主题分类统计列表 (List[Dict]), 每个元素包含 "topic" (String) 和 "count" (Int)。例如: [{{"topic": "AI产品", "count": 5}}]。请确保 "topic" 使用中文。
        - key_highlights: 重点想法列表 (List[String]), 选出3-5个最有价值的想法，格式为 "标题 - 一句话评价"。请确保评价使用中文。
        - weekly_synthesis: 本周关注点总结 (String), 一段话总结用户本周的思考方向。请确保使用中文。
        
        只返回 JSON 字符串。
        """
        
        response = dashscope.Generation.call(
            model=settings.QWEN_CHAT_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            result_format='message',
        )
        
        return self._parse_json_response(response)

    def _parse_json_response(self, response) -> Dict[str, Any]:
        """
        Helper to parse JSON from LLM response
        """
        if response.status_code == HTTPStatus.OK:
            content = response.output.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Extract JSON block
            start_idx = content.find("{")
            end_idx = content.rfind("}")
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                content = content[start_idx:end_idx+1]
                
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error in _parse_json_response: {e}, Raw content: {content}")
                return {"error": "Failed to parse JSON", "raw": content}
        else:
             raise Exception(f"LLM Chat Failed: {response.code} - {response.message}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts using text-embedding-v4
        """
        if not texts:
            return []
            
        if not DASHSCOPE_AVAILABLE:
            # Return dummy embeddings (e.g. 1024 dimension)
            # Just random or zero
            return [[0.1] * 1024 for _ in texts]

        resp = dashscope.TextEmbedding.call(
            model=settings.QWEN_EMBED_MODEL,
            input=texts
        )
        
        if resp.status_code == HTTPStatus.OK:
            # embeddings are in resp.output.embeddings
            # Each item has 'embedding' and 'text_index'
            # Sort by text_index to ensure order matches input
            embeddings_list = resp.output.embeddings if hasattr(resp.output, 'embeddings') else resp.output['embeddings']
            sorted_embeddings = sorted(embeddings_list, key=lambda x: x['text_index'])
            return [item['embedding'] for item in sorted_embeddings]
        else:
            raise Exception(f"Embedding Failed: {resp.code} - {resp.message}")

llm_service = LLMService()
