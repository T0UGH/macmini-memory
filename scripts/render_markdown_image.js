#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function inlineFormat(text) {
  let s = escapeHtml(text);
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  s = s.replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2">$1</a>');
  s = s.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1">$1</a>');
  return s;
}

function markdownToHtml(md) {
  const lines = md.replace(/\r\n/g, '\n').split('\n');
  let html = [];
  let inList = false;
  let inCode = false;
  let codeLines = [];
  let paragraph = [];

  function flushParagraph() {
    if (paragraph.length) {
      html.push(`<p>${inlineFormat(paragraph.join(' '))}</p>`);
      paragraph = [];
    }
  }

  function closeList() {
    if (inList) {
      html.push('</ul>');
      inList = false;
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.startsWith('```')) {
      flushParagraph();
      closeList();
      if (!inCode) {
        inCode = true;
        codeLines = [];
      } else {
        html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
        inCode = false;
      }
      continue;
    }
    if (inCode) {
      codeLines.push(rawLine);
      continue;
    }

    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      closeList();
      continue;
    }

    const heading = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = heading[1].length;
      html.push(`<h${level}>${inlineFormat(heading[2])}</h${level}>`);
      continue;
    }

    const bullet = trimmed.match(/^[-*+]\s+(.*)$/);
    if (bullet) {
      flushParagraph();
      if (!inList) {
        html.push('<ul>');
        inList = true;
      }
      html.push(`<li>${inlineFormat(bullet[1])}</li>`);
      continue;
    }

    const quote = trimmed.match(/^>\s?(.*)$/);
    if (quote) {
      flushParagraph();
      closeList();
      html.push(`<blockquote>${inlineFormat(quote[1])}</blockquote>`);
      continue;
    }

    paragraph.push(trimmed);
  }

  flushParagraph();
  closeList();
  if (inCode) {
    html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
  }
  return html.join('\n');
}

async function main() {
  const input = process.argv[2];
  const output = process.argv[3] || input.replace(/\.md$/i, '.png');
  if (!input) {
    console.error('Usage: render_markdown_image.js <input.md> [output.png]');
    process.exit(1);
  }

  const md = fs.readFileSync(input, 'utf8');
  const body = markdownToHtml(md);
  const title = path.basename(input);
  const html = `<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>${escapeHtml(title)}</title><style>:root{--bg:#f5f7fb;--paper:#ffffff;--text:#18212f;--muted:#5f6b7a;--border:#e5e9f0;--accent:#2563eb}*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#eef4ff 0%,var(--bg) 100%);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif}.page{width:1200px;margin:0 auto;padding:48px}.card{background:var(--paper);border:1px solid var(--border);border-radius:24px;box-shadow:0 18px 50px rgba(15,23,42,.08);padding:52px 60px}.meta{font-size:18px;color:var(--muted);margin-bottom:18px}h1,h2,h3,h4,h5,h6{margin:1.1em 0 .55em;line-height:1.3}h1{font-size:42px}h2{font-size:32px;border-top:1px solid var(--border);padding-top:22px}h3{font-size:26px}h4{font-size:22px}p,li,blockquote,pre{font-size:22px;line-height:1.75}p{margin:.5em 0}ul{margin:.3em 0 1em 1.2em;padding:0}li{margin:.25em 0}blockquote{margin:1em 0;padding:16px 20px;border-left:6px solid var(--accent);background:#f8fbff;color:#24364d;border-radius:0 12px 12px 0}code{background:#f1f5f9;border:1px solid #e2e8f0;border-radius:8px;padding:2px 8px;font-size:.9em;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}pre{white-space:pre-wrap;word-break:break-word;background:#0f172a;color:#e2e8f0;padding:18px 22px;border-radius:16px;overflow:hidden}pre code{background:transparent;border:0;padding:0;color:inherit}a{color:var(--accent);text-decoration:none}</style></head><body><div class="page"><div class="card"><div class="meta">Markdown 图片副本 · ${escapeHtml(title)}</div>${body}</div></div></body></html>`;

  const tmpHtml = path.join(path.dirname(output), `.${path.basename(output)}.tmp.html`);
  fs.writeFileSync(tmpHtml, html, 'utf8');
  execFileSync('playwright', ['screenshot', '--device=Desktop Chrome HiDPI', '--full-page', `file://${tmpHtml}`, output], { stdio: 'inherit' });
  fs.unlinkSync(tmpHtml);
  console.log(output);
}

main().catch(err => { console.error(err); process.exit(1); });
