"""
智能备课助手 — FastAPI Web 服务

提供聊天 API、Vault 浏览 API、静态文件服务。
一键启动后，通过浏览器访问 http://localhost:8000
"""
import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import (
    StreamingResponse,
    JSONResponse,
    FileResponse,
    HTMLResponse,
)
from fastapi.staticfiles import StaticFiles
from agent.core import LessonPrepAgent
from agent import vault

app = FastAPI(title="智能备课助手", version="1.0.0")

agent = LessonPrepAgent()

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index():
    """主页"""
    html_file = STATIC_DIR / "index.html"
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "智能备课助手"}


@app.post("/api/chat")
async def chat(request: Request):
    """聊天接口（流式输出）"""
    body = await request.json()
    user_input = body.get("message", "")
    history = body.get("history", [])

    if not user_input.strip():
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    async def generate():
        loop = asyncio.get_event_loop()
        gen = agent.process_stream(user_input, history)
        for chunk in gen:
            await asyncio.sleep(0)
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/vault/tree")
async def vault_tree():
    """获取仓库目录树"""
    return vault.get_vault_tree()


@app.get("/api/vault/notes")
async def vault_notes(category: str = ""):
    """获取某一类别下的笔记列表"""
    if category:
        return vault.list_notes(category)
    return {}


@app.get("/api/vault/note")
async def vault_note(category: str = "", filename: str = ""):
    """读取一篇笔记的完整内容"""
    content = vault.read_note(category, filename)
    if content is None:
        return JSONResponse({"error": "笔记不存在"}, status_code=404)
    return {"category": category, "filename": filename, "content": content}


@app.delete("/api/vault/note")
async def delete_note(category: str = "", filename: str = ""):
    """删除一篇笔记（移到回收站逻辑）"""
    import shutil
    filepath = vault.VAULT_DIR / category / filename
    if not filepath.exists():
        return JSONResponse({"error": "笔记不存在"}, status_code=404)
    trash = vault.VAULT_DIR / ".trash" / category
    trash.mkdir(parents=True, exist_ok=True)
    shutil.move(str(filepath), str(trash / filename))
    vault.update_index(category)
    return {"status": "deleted"}


# 静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("=" * 55)
    print("  智能备课助手 Web 服务启动中...")
    print(f"  本地访问: http://localhost:{port}")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=port)
