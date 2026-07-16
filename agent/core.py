"""
智能备课助手 — Agent 核心模块

负责会话管理、意图识别、Skill 路由、LLM 调用。
"""
import re
import json
from datetime import datetime
from openai import OpenAI
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    MAX_HISTORY_MESSAGES,
)
from agent import vault, skills


class LessonPrepAgent:
    def __init__(self):
        self.client = None
        if DEEPSEEK_API_KEY:
            self.client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
            )
        vault.init_vault()

    def _ensure_client(self):
        """确保客户端已初始化，否则抛出友好错误"""
        if self.client is None:
            raise RuntimeError(
                "未配置 DeepSeek API Key，聊天功能暂时不可用。\n"
                "请设置环境变量 DEEPSEEK_API_KEY 后重启服务。"
            )

    def _call_llm(self, system_prompt: str, user_message: str, history: list[dict] = None) -> str:
        """同步调用 LLM"""
        self._ensure_client()
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-MAX_HISTORY_MESSAGES:])
        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    def _call_llm_stream(self, system_prompt: str, user_message: str, history: list[dict] = None):
        """流式调用 LLM，逐块返回内容"""
        self._ensure_client()
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-MAX_HISTORY_MESSAGES:])
        messages.append({"role": "user", "content": user_message})

        stream = self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def process(self, user_input: str, history: list[dict] = None) -> dict:
        """处理用户输入，返回结果"""
        if history is None:
            history = []

        intent = skills.recognize_intent(user_input)

        if intent == "chat":
            result = skills.chat(user_input, history)
            full_response = self._call_llm(result["system"], result["user"], history)
            return {
                "response": full_response,
                "intent": "chat",
                "saved_file": None,
            }

        skill_funcs = {
            "prepare_lesson": skills.prepare_lesson,
            "generate_slides": skills.generate_slides,
            "generate_exercises": skills.generate_exercises,
            "teaching_research": skills.teaching_research,
            "update_vault": None,
        }

        skill_func = skill_funcs.get(intent)
        if skill_func is None:
            if intent == "update_vault":
                return self._do_update_vault()
            result = skills.chat(user_input, history)
            full_response = self._call_llm(result["system"], result["user"], history)
            return {
                "response": full_response,
                "intent": "chat",
                "saved_file": None,
            }

        result = skill_func(user_input)
        full_response = self._call_llm(result["system"], result["user"], history)

        saved_file = None
        if result.get("save_category"):
            saved_file = self._auto_save(result, full_response, user_input)

        return {
            "response": full_response,
            "intent": intent,
            "saved_file": saved_file,
        }

    def process_stream(self, user_input: str, history: list[dict] = None):
        """流式处理用户输入，逐块返回内容"""
        if history is None:
            history = []

        intent = skills.recognize_intent(user_input)

        if intent == "chat":
            result = skills.chat(user_input, history)
            full_text = ""
            for chunk in self._call_llm_stream(result["system"], result["user"], history):
                full_text += chunk
                yield {"type": "text", "content": chunk}
            yield {"type": "done", "intent": "chat", "saved_file": None}
            return

        if intent == "update_vault":
            update_result = self._do_update_vault()
            yield {"type": "text", "content": update_result["response"]}
            yield {"type": "done", "intent": "update_vault", "saved_file": None}
            return

        skill_funcs = {
            "prepare_lesson": skills.prepare_lesson,
            "generate_slides": skills.generate_slides,
            "generate_exercises": skills.generate_exercises,
            "teaching_research": skills.teaching_research,
        }

        skill_func = skill_funcs.get(intent)
        if skill_func is None:
            result = skills.chat(user_input, history)
            full_text = ""
            for chunk in self._call_llm_stream(result["system"], result["user"], history):
                full_text += chunk
                yield {"type": "text", "content": chunk}
            yield {"type": "done", "intent": "chat", "saved_file": None}
            return

        result = skill_func(user_input)
        full_text = ""
        for chunk in self._call_llm_stream(result["system"], result["user"], history):
            full_text += chunk
            yield {"type": "text", "content": chunk}

        saved_file = None
        if result.get("save_category"):
            saved_file = self._auto_save(result, full_text, user_input)

        yield {"type": "done", "intent": intent, "saved_file": saved_file}

    def _auto_save(self, skill_result: dict, response_text: str, user_input: str) -> dict | None:
        """自动保存生成的内容到 vault"""
        category = skill_result.get("save_category")
        prefix = skill_result.get("save_prefix", "笔记")
        if not category:
            return None

        # 从用户输入提取标题
        title = user_input.strip()
        title = re.sub(r'^[是为根据请帮]', '', title)
        title = re.sub(r'[生编]写|生成|创建|制作|备一下|一下', '', title)
        title = title.strip()
        if len(title) > 40:
            title = title[:40]
        if not title:
            title = f"{prefix}_{datetime.now().strftime('%m%d_%H%M')}"

        # 清理文件名
        filename = re.sub(r'[\\/:*?"<>|]', '-', title)
        filename = filename.strip().rstrip('.') + ".md"

        meta = {"title": title}
        filepath = vault.write_note(category, filename, response_text, meta)
        vault.update_index(category)

        return {
            "category": category,
            "filename": filename,
            "relative_path": f"{category}/{filename}",
        }

    def _do_update_vault(self) -> dict:
        """执行仓库维护"""
        from config import CATEGORIES
        updated = []
        for cat_name in CATEGORIES:
            vault.update_index(cat_name)
            updated.append(cat_name)

        report = "## 仓库维护完成\n\n"
        report += "| 目录 | 状态 |\n|------|------|\n"
        for cat in updated:
            notes = vault.list_notes(cat)
            report += f"| {cat}/ | 已更新 ({len(notes)} 篇笔记) |\n"
        report += f"\n共维护 {len(updated)} 个目录。"

        return {"response": report, "intent": "update_vault", "saved_file": None}
