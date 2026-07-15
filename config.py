"""
智能备课助手 — Web 应用配置
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# Vault 仓库路径
VAULT_DIR = BASE_DIR / "vault"

# Agent 配置
MAX_HISTORY_MESSAGES = 20
SYSTEM_CONFIG_DIR = VAULT_DIR / "system_config"

# 教师背景文件
TEACHER_PROFILE = VAULT_DIR / "1_关于我" / "教师背景.md"
MEMORY_FILE = SYSTEM_CONFIG_DIR / "memory.md"
TEMPLATES_FILE = SYSTEM_CONFIG_DIR / "templates.md"

# 类别目录映射
CATEGORIES = {
    "1_关于我": "教师个人信息与教学背景",
    "2_教学灵感": "教学创意与案例素材",
    "3_课程": "课程大纲与进度表",
    "4_教案": "逐课教案",
    "5_课件": "PPT课件大纲",
    "6_习题": "练习题与试卷",
    "7_教学反思": "课后反思与改进",
    "8_教研": "教学研究与前沿动态",
    "9_学生": "学情记录与分析",
    "临时工作区": "草稿暂存",
}

# 技能触发关键词
SKILL_KEYWORDS = {
    "prepare_lesson": ["备课", "写教案", "备一下", "教案", "教学设计", "prepare a lesson"],
    "generate_slides": ["课件", "PPT", "课件大纲", "做ppt", "幻灯片", "slides"],
    "generate_exercises": ["出题", "出几道", "出一些", "习题", "练习题", "计算题", "试卷", "考试", "测试题", "exercises", "exam"],
    "teaching_research": ["教学研究", "教研", "搜资源", "查前沿", "找案例", "research", "前沿"],
    "update_vault": ["更新仓库", "更新索引", "整理仓库", "修复链接"],
}
