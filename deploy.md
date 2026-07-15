# 智能备课助手 — 部署与使用指南

## 一、快速启动（本地运行）

### 1. 环境要求
- Python 3.10+
- DeepSeek API Key（注册地址：https://platform.deepseek.com）

### 2. 设置 API Key
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxx"

# Windows CMD
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 安装依赖并启动
```bash
cd web_app
pip install -r requirements.txt
python server.py
```

### 4. 打开浏览器
访问 http://localhost:8000

---

## 二、公网部署方案（评委可通过互联网访问）

### 方案 A：ngrok 内网穿透（免费，推荐用于评审）

**原理**：把本地 8000 端口映射到公网，生成一个任何人都能访问的网址。

#### A1. 获取固定域名（推荐，网址永久不变）

1. 注册 ngrok 账号：https://dashboard.ngrok.com/signup（用 GitHub/Google 即可）
2. 登录后在页面左侧找到 **Domains**，创建一个免费静态域名
   - 免费版可申请 1 个固定域名，如 `xxxxx.ngrok-free.app`
3. 获取 authtoken（首页顶部就有）
4. 配置并启动：
   ```bash
   ngrok config add-authtoken <你的authtoken>
   ngrok http --domain=你的固定域名.ngrok-free.app 8000
   ```
5. 只要不关闭窗口，网址永远不变，评委随时可访问
6. 将这个固定域名作为「测试链接」提交给大赛

#### A2. 临时测试（每次重启网址会变）

```bash
ngrok http 8000
# 输出形如 https://abc123.ngrok-free.app → 这个链接只在本次运行有效
```


### 方案 B：Railway 云端部署（免费，24小时在线，推荐用于大赛）

Railway 提供免费额度，部署后智能体**24 小时在线**，评委随时打开网址就能用。

#### 部署步骤（5 分钟完成）

**前置准备**：一个 GitHub 账号（用于关联 Railway，免费注册 github.com）

**1. 将代码推送到 GitHub**
```bash
# 在 web_app 目录下
git init
git add .
git commit -m "智能备课助手 Web 应用"
git remote add origin https://github.com/你的用户名/lesson-prep-agent.git
git push -u origin main
```

**2. 在 Railway 部署**
- 打开 https://railway.com → 用 GitHub 账号登录
- 点击 **New Project** → **Deploy from GitHub repo**
- 选择刚才推送的仓库
- Railway 自动检测 Python 项目并部署

**3. 设置环境变量**
在 Railway 项目面板 → Variables → 添加：
```
DEEPSEEK_API_KEY = sk-你的DeepSeek_API_Key
```

**4. 获取测试链接**
Railway 自动分配域名，形如：
`https://lesson-prep-agent.up.railway.app`

将这个网址提交给大赛作为「测试链接」。

#### Railway 免费额度
- 每月 $5 免费额度
- 约可支撑 3000+ 次 AI 对话
- 部署后自动休眠（访问时自动唤醒，约 10 秒冷启动）

### 方案 C：本地 + ngrok 内网穿透（需保持电脑开机）

```bash
# 1. 先启动 Web 服务
python server.py

# 2. 另开一个终端，用 ngrok 暴露服务
ngrok http --domain=你的固定域名.ngrok-free.app 8000
```

> ⚠️ 此方案要求本地电脑持续开机，适合短时间演示。长期评审建议用方案 B。

### 方案 D：使用超星大赛平台

大赛官方提供智能体开发平台和算力资源，可直接使用超星泛雅平台部署，无需自己管理服务器。

---

## 三、配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 必填 |
| `DEEPSEEK_BASE_URL` | API 地址 | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | 模型名称 | deepseek-chat |

### 切换到其他 LLM

本项目使用 OpenAI 兼容接口，可通过修改环境变量切换到其他模型：

```bash
# 使用 OpenAI
$env:DEEPSEEK_API_KEY="sk-..."
$env:DEEPSEEK_BASE_URL="https://api.openai.com/v1"
$env:DEEPSEEK_MODEL="gpt-4o"

# 使用通义千问
$env:DEEPSEEK_API_KEY="sk-..."
$env:DEEPSEEK_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:DEEPSEEK_MODEL="qwen-turbo"
```

---

## 四、参赛材料对照

| 大赛要求 | 本项目对应 |
|---------|-----------|
| 教学智能体建设说明书 | 参见 `建设说明书.md` |
| 展示视频 (6-10分钟) | 录屏演示智能体功能 |
| 测试链接 | ngrok 公网 URL 或服务器地址 |
| 原创性证明 | 本目录全部代码 + 技术路线图 |
| 申报组别 | 普通高校赛道 → 教学辅助智能体 |

---

## 五、项目结构

```
web_app/
├── server.py              # FastAPI Web 服务
├── config.py              # 配置管理
├── requirements.txt       # Python 依赖
├── run.bat                # Windows 启动脚本
├── agent/
│   ├── core.py            # Agent 核心（对话管理、LLM 调用）
│   ├── skills.py          # 5 个 Skills 实现
│   └── vault.py           # 备课仓库文件管理
├── static/
│   ├── index.html         # 前端聊天界面
│   ├── style.css          # 样式
│   └── app.js             # 前端交互逻辑
├── vault/                 # 备课仓库（数据存储）
│   ├── 1_关于我/ ~ 9_学生/
│   ├── 临时工作区/
│   └── system_config/
└── deploy.md              # 本文件
```
