import streamlit as st
import json
import urllib.parse
import re

st.set_page_config(layout="wide", page_title="Auto Task")

# --- 1. 你最强的 v15.0 JS 脚本模板 (带全平台适配) ---
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

    function getInputBox() {{
        return document.querySelector('#prompt-textarea, div[contenteditable="true"], textarea, .n-input__textarea-el, [placeholder*="输入"], [placeholder*="提问"]');
    }}

    function getSendBtn() {{
        let btns = Array.from(document.querySelectorAll('button, [role="button"], i'));
        return btns.find(b => {{
            const t = (b.innerText || b.ariaLabel || b.className || "").toLowerCase();
            return (t.includes('发') || t.includes('send')) && !t.includes('新') && !t.includes('stop') && b.offsetParent !== null;
        }});
    }}

    function isGenerating() {{
        return Array.from(document.querySelectorAll('button, [role="button"]')).some(b => {{
            const t = (b.innerText || b.ariaLabel || "").toLowerCase();
            return t.includes('stop') || t.includes('停止') || t.includes('generating');
        }});
    }}

    showStatus("🤖 纹身大师自动化启动...");
    for (let i = 0; i < tasks.length; i++) {{
        if (window.kill) break;
        showStatus("✍️ 正在输入任务: " + (i+1) + " / " + tasks.length);
        let box = getInputBox();
        if (!box) {{ showStatus("❌ 找不到输入框", "#ef4444"); break; }}
        box.focus();
        document.execCommand('insertText', false, tasks[i]);
        await new Promise(r => setTimeout(r, 1000));
        box.dispatchEvent(new Event('input', {{ bubbles: true }}));
        let sendBtn = getSendBtn();
        if (sendBtn) sendBtn.click();
        
        if (i < tasks.length - 1) {{
            await new Promise(r => setTimeout(r, 3000));
            let waitTime = 0;
            while(isGenerating() && !window.kill) {{
                showStatus("🎨 AI 作画中 (" + waitTime + "s)...", "#8b5cf6");
                await new Promise(r => setTimeout(r, 1000));
                waitTime++;
                if (waitTime > 200) break;
            }}
            showStatus("⏳ 冷却中...", "#f59e0b");
            await new Promise(r => setTimeout(r, 5000));
        }}
    }}
    showStatus("🎉 任务全部完成！", "#10b981");
}})();"""

# --- 2. 界面设计 ---
st.title("🤖 自动化任务分发中控")

default_text = st.session_state.get('auto_input_cache', "")
user_input = st.text_area("在此粘贴或编辑提示词：", value=default_text, height=350)

if st.button("🚀 生成全能脚本 (F12)", type="primary", use_container_width=True):
    # 【智能拆分】：使用正则匹配 **方案一：** 这种块
    # 逻辑：只要看到“方案”和冒号，就认为是一个新任务的开始
    blocks = re.split(r'\*\*方案[一二三四五六七八九十\d]+[:：].*?\*\*', user_input)
    
    # 清洗掉多余的星号和换行，变成适合跑图的单行
    task_list = [b.strip().replace('* ', '').replace('\n', ' ') for b in blocks if len(b.strip()) > 5]
    
    if task_list:
        st.divider()
        st.subheader(f"📦 待处理任务: {len(task_list)} 条")
        
        # 生成 JS 代码
        final_js = generate_v15_script(task_list)
        
        # 醒目的操作指引
        st.warning("👉 **操作指引**：\n1. 点击下方代码框右上角的 **复制** 按钮。\n2. 打开跑图网站，按键盘上的 **F12**。\n3. 点击 **Console (控制台)**，粘贴代码并回车。")
        st.code(final_js, language="javascript")
    else:
        st.error("无法识别任务，请确保格式包含类似 '**方案一：**' 的字样。")
