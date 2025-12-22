import streamlit as st
import json
import urllib.parse
import re

st.set_page_config(layout="wide", page_title="Automation")

# --- 1. 还原你最强的 MagicPrompt v15.0 全平台适配逻辑 ---
def generate_v15_script(prompts):
    encoded_data = urllib.parse.quote(json.dumps(prompts))
    return f"""(async function() {{
    window.kill = false;
    const tasks = JSON.parse(decodeURIComponent("{encoded_data}"));
    
    function showStatus(text, color = "#6366f1") {{
        let el = document.getElementById('magic-status-bar') || document.createElement('div');
        el.id = 'magic-status-bar';
        el.style.cssText = "position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:999999; padding:10px 20px; border-radius:30px; font-family:sans-serif; font-size:14px; font-weight:bold; box-shadow:0 10px 25px rgba(0,0,0,0.2); background:"+color+"; color:#fff; transition: all 0.3s;";
        if(!document.getElementById('magic-status-bar')) document.body.appendChild(el);
        el.textContent = text;
    }}

    // v15.0 核心：全能输入框探测器 (含 ChatGPT / Doubao / 镜像站 / Gemini)
    function getInputBox() {{
        return document.querySelector(
            '#prompt-textarea, ' + 
            'div[contenteditable="true"], ' + 
            'textarea, ' + 
            '.n-input__textarea-el, ' + 
            '[placeholder*="输入"], [placeholder*="提问"]'
        );
    }}

    // v15.0 核心：全能发送按钮探测器 (智能排除停止按钮)
    function getSendBtn() {{
        let btns = Array.from(document.querySelectorAll('button, [role="button"], i'));
        return btns.find(b => {{
            const t = (b.innerText || b.ariaLabel || b.className || "").toLowerCase();
            const isSend = t.includes('发') || t.includes('send') || (b.tagName === 'I' && t.includes('send')) || b.getAttribute('data-testid') === 'send-button';
            const isStop = t.includes('stop') || t.includes('停止');
            return isSend && !isStop && b.offsetParent !== null && !b.disabled;
        }});
    }}

    function isGenerating() {{
        return Array.from(document.querySelectorAll('button, [role="button"]')).some(b => {{
            const t = (b.innerText || b.ariaLabel || "").toLowerCase();
            return t.includes('stop') || t.includes('停止') || t.includes('generating');
        }});
    }}

    showStatus("🤖 纹身大师 v15.0 全能中控启动...");
    for (let i = 0; i < tasks.length; i++) {{
        if (window.kill) break;
        showStatus("✍️ 正在输入: " + (i+1) + " / " + tasks.length, "#3b82f6");
        let box = getInputBox();
        if (!box) {{ showStatus("❌ 找不到输入框 (请点一下对话框)", "#ef4444"); break; }}
        
        box.focus();
        document.execCommand('insertText', false, tasks[i]);
        await new Promise(r => setTimeout(r, 1000));
        box.dispatchEvent(new Event('input', {{ bubbles: true }}));
        
        let sendBtn = getSendBtn();
        if (sendBtn) sendBtn.click();
        
        if (i < tasks.length - 1) {{
            await new Promise(r => setTimeout(r, 3000));
            let wait = 0;
            while(isGenerating() && !window.kill) {{
                showStatus("🎨 AI 作画中 (" + wait + "s)...", "#8b5cf6");
                await new Promise(r => setTimeout(r, 1000));
                wait++;
                if (wait > 180) break;
            }}
            showStatus("⏳ 冷却 5s 以防频率过快...", "#f59e0b");
            await new Promise(r => setTimeout(r, 5000));
        }}
    }}
    showStatus("🎉 任务全部完成！", "#10b981");
}})();"""

st.title("🤖 自动化任务分发中控")

# --- 接收逻辑 ---
default_text = st.session_state.get('auto_input_cache', "")
user_input = st.text_area("检查待处理的提示词：", value=default_text, height=350)

# --- 智能拆分逻辑 (修复 11 个任务的问题) ---
if st.button("🚀 生成全能适配脚本 (去目标站按F12)", type="primary", use_container_width=True):
    # 改为按“方案”关键字拆分
    import re
    blocks = re.split(r'\*\*方案[一二三四五六七八九十\d]+[:：].*?\*\*', user_input)
    task_list = [b.strip().replace('* ', '').replace('\n', ' ') for b in blocks if len(b.strip()) > 5]
    
    if task_list:
        st.divider()
        st.subheader(f"📦 待处理任务: {len(task_list)} 条")
        
        # 指引
        st.warning("👉 **复制后操作步骤**：\\n1. 点击下方代码框右上角复制 \\n2. 打开绘图站(ChatGPT/豆包)按 **F12** \\n3. 找到 **Console (控制台)** 粘贴并回车。")
        
        # 脚本展示
        js_code = generate_v15_script(task_list)
        st.code(js_code, language="javascript")
    else:
        st.error("无法识别内容，请确保包含 '**方案一：**' 字样")

if st.button("🗑️ 清空当前任务流"):
    st.session_state.auto_input_cache = ""
    st.rerun()
