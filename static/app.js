/**
 * 智能备课助手 — 前端交互逻辑
 */

let isStreaming = false;
let conversationHistory = [];
let currentAiMessage = null;

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
  loadVaultTree();
  document.getElementById('userInput').focus();
});

// ========== 侧边栏 ==========
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('collapsed');
}

// ========== 快捷操作 ==========
function quickAction(text) {
  const input = document.getElementById('userInput');
  input.value = text;
  sendMessage();
}

// ========== 发送消息 ==========
async function sendMessage() {
  if (isStreaming) return;

  const input = document.getElementById('userInput');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';
  input.style.height = 'auto';
  document.getElementById('sendBtn').disabled = true;

  // 隐藏欢迎消息
  const welcome = document.querySelector('.welcome-message');
  if (welcome) welcome.remove();

  // 添加用户消息
  addMessage('user', message);
  conversationHistory.push({ role: 'user', content: message });

  // 添加 AI 消息占位
  currentAiMessage = addMessage('ai', '', true);

  // 流式请求
  try {
    isStreaming = true;
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history: conversationHistory }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let savedFile = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = JSON.parse(line.slice(6));

        if (data.type === 'text') {
          fullText += data.content;
          updateMessageContent(currentAiMessage, fullText);
        } else if (data.type === 'done') {
          // 处理 done 事件
          if (data.saved_file) {
            savedFile = data.saved_file;
            addSaveBadge(currentAiMessage, data.saved_file);
          }
        }
      }
    }

    conversationHistory.push({ role: 'assistant', content: fullText });

    if (savedFile) {
      loadVaultTree();
    }
  } catch (err) {
    console.error('Error:', err);
    updateMessageContent(currentAiMessage, '抱歉，请求出错了，请稍后重试。');
  } finally {
    isStreaming = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('userInput').focus();
  }
}

// ========== 消息 UI ==========
function addMessage(role, content, isStreaming = false) {
  const container = document.getElementById('chatMessages');
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? 'U' : 'AI';

  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';

  if (isStreaming) {
    bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
  } else {
    bubble.innerHTML = renderMarkdown(content);
  }

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(bubble);
  container.appendChild(msgDiv);

  scrollToBottom();
  return msgDiv;
}

function updateMessageContent(msgDiv, text) {
  const bubble = msgDiv.querySelector('.msg-bubble');
  if (!bubble) return;
  bubble.innerHTML = renderMarkdown(text) || '';
  scrollToBottom();
}

function addSaveBadge(msgDiv, savedFile) {
  const bubble = msgDiv.querySelector('.msg-bubble');
  if (!bubble || !savedFile) return;

  const badge = document.createElement('div');
  badge.className = 'save-badge';
  badge.innerHTML = '已保存到仓库';
  badge.title = `${savedFile.category}/${savedFile.filename}`;
  badge.onclick = () => openNote(savedFile.category, savedFile.filename);
  bubble.appendChild(badge);
}

// ========== Markdown 渲染（简易版） ==========
function renderMarkdown(text) {
  if (!text) return '';

  let html = text;

  // 代码块
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="language-${lang}">${escapeHtml(code.trim())}</code></pre>`;
  });

  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // 标题
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // 粗体/斜体
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // 引用块
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

  // 表格
  html = html.replace(/\n(\|.+\|)\n\|[-| :]+\|\n((?:\|.+\|\n?)*)/g, (_, header, body) => {
    const headers = header.split('|').filter(h => h.trim()).map(h => `<th>${h.trim()}</th>`).join('');
    const rows = body.trim().split('\n').map(row => {
      const cells = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
      return `<tr>${cells}</tr>`;
    }).join('');
    return `\n<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>\n`;
  });

  // 有序列表
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
  // 无序列表
  html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');

  // 水平线
  html = html.replace(/^---+$/gm, '<hr>');

  // 段落（连续的非空行）
  html = html.replace(/\n\n+/g, '</p><p>');
  html = '<p>' + html + '</p>';

  // 清理空段落
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p><h([1-6])>/g, '<h$1>');
  html = html.replace(/<\/h([1-6])><\/p>/g, '</h$1>');
  html = html.replace(/<p><pre>/g, '<pre>');
  html = html.replace(/<\/pre><\/p>/g, '</pre>');
  html = html.replace(/<p><table>/g, '<table>');
  html = html.replace(/<\/table><\/p>/g, '</table>');
  html = html.replace(/<p><blockquote>/g, '<blockquote>');
  html = html.replace(/<\/blockquote><\/p>/g, '</blockquote>');

  return html;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ========== Vault Tree ==========
async function loadVaultTree() {
  try {
    const resp = await fetch('/api/vault/tree');
    const tree = await resp.json();
    renderVaultTree(tree);
  } catch (err) {
    console.error('Failed to load vault tree:', err);
  }
}

function renderVaultTree(tree) {
  const container = document.getElementById('vaultTree');
  if (!container) return;

  let html = '';
  const icons = {
    '1_关于我': '👤', '2_教学灵感': '💡', '3_课程': '📋',
    '4_教案': '📝', '5_课件': '🖥', '6_习题': '📐',
    '7_教学反思': '🔄', '8_教研': '🔬', '9_学生': '👥',
    '临时工作区': '📦'
  };

  for (const [cat, files] of Object.entries(tree)) {
    const icon = icons[cat] || '📁';
    const catId = cat.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_');
    html += `<div class="vault-category">`;
    html += `<div class="vault-cat-header" onclick="toggleVaultCat('${catId}')">`;
    html += `<span class="arrow" id="arrow_${catId}">▶</span>`;
    html += `<span class="vault-cat-icon">${icon}</span>`;
    html += `<span>${cat}/</span>`;
    html += `<span style="color:#6b7280;font-size:11px;margin-left:auto">${files.length}</span>`;
    html += `</div>`;
    html += `<div class="vault-files" id="files_${catId}">`;
    for (const file of files) {
      html += `<div class="vault-file" onclick="openNote('${cat}','${file}')" title="${file}">`;
      html += `📄 ${file.replace('.md', '')}`;
      html += `</div>`;
    }
    html += `</div></div>`;
  }

  container.innerHTML = html;
}

function toggleVaultCat(catId) {
  const files = document.getElementById('files_' + catId);
  const arrow = document.getElementById('arrow_' + catId);
  if (!files || !arrow) return;
  files.classList.toggle('open');
  arrow.classList.toggle('open');
}

// ========== 笔记预览 ==========
async function openNote(category, filename) {
  try {
    const resp = await fetch(`/api/vault/note?category=${encodeURIComponent(category)}&filename=${encodeURIComponent(filename)}`);
    const data = await resp.json();
    if (data.error) {
      alert('笔记不存在');
      return;
    }

    const panel = document.getElementById('previewPanel');
    document.getElementById('previewTitle').textContent = filename.replace('.md', '');
    document.getElementById('previewContent').innerHTML = renderMarkdown(data.content);
    panel.style.display = 'flex';

    // 高亮当前文件
    document.querySelectorAll('.vault-file.active').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.vault-file').forEach(el => {
      if (el.textContent.includes(filename.replace('.md', ''))) {
        el.classList.add('active');
      }
    });
  } catch (err) {
    console.error('Failed to open note:', err);
  }
}

function closePreview() {
  document.getElementById('previewPanel').style.display = 'none';
}

// ========== 输入辅助 ==========
function handleKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
}

function scrollToBottom() {
  const container = document.getElementById('chatMessages');
  setTimeout(() => {
    container.scrollTop = container.scrollHeight;
  }, 50);
}
