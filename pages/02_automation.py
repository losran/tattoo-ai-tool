import streamlit as st
import json
import urllib.parse

st.set_page_config(layout="wide", page_title="Auto Task")

# --- 1. JS 脚本模板 (你的 v15.0 顶级逻辑) ---
def generate_magic_code(prompts):
    encoded = urllib.parse.quote(json.dumps(prompts))
    return f"""(async function() {{
    window.kill = false;
    const tasks = JSON.parse(decodeURIComponent("{encoded}"));
    function showStatus(t, c="#6366f1") {{
        let e = document.getElementById('magic-status-bar') || document.createElement('div');
        e.id = 'magic-status-bar';
        e.style.cssText = "position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:999999;padding:10px 20px;border-radius:30px;font-family:sans-serif;font-size:14px;font-weight:bold;box-shadow:0 10px 25px rgba(0,0,0,0.2);background:"+c+";color:#fff;transition:0.3s;";
        if(!document.getElementById('magic-status-bar')) document.body.appendChild(e);
        e.textContent = t;
    }}
    function getInput() {{ return document.querySelector('#prompt-textarea, div[contenteditable="true"], textarea, .n-input__textarea-el'); }}
    function isGen() {{ return Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('停止') || b.innerText.includes('Stop')); }}
    
    showStatus("🚀 纹身自动化启动...");
    for (let i=0; i<tasks.length; i++) {{
        if(window.kill) break;
        showStatus("✍️ 正在输入 ("+(i+1)+"/"+tasks.length+")");
        let b = getInput(); if(!b) break;
        b.focus(); document.execCommand('insertText', false, tasks[i]);
        await new Promise(r => setTimeout(r, 1000));
        b.dispatchEvent(new Event('input', {{bubbles:true}}));
        b.dispatchEvent(new KeyboardEvent('keydown', {{bubbles:true, key:'Enter', keyCode:13}}));
        
        if(i < tasks.length-1) {{
            await new Promise(r => setTimeout(r, 3000));
            while(isGen() && !window.kill) {{ await new Promise(r => setTimeout(r, 1000)); }}
            await new Promise(r => setTimeout(r, 5000));
        }}
    }}
    showStatus("🎉 全部完成！", "#10b981");
}})();"""

# --- 2. UI 界面 ---
st.title("🤖 自动化任务分发中控")

# 优先级：如果有来自第二功能的缓存就用它，否则为空
default_text = st.session_state.get('auto_input_cache', "")

# 唯一的核心输入框 (既支持搬运，也支持传送)
user_input = st.text_area("在此粘贴或编辑提示词（每行一条）：", value=default_text, height=300, placeholder="提示词1\n提示词2...")

if st.button("🚀 生成全能脚本 (F12)", type="primary", use_container_width=True):
    # 清洗数据
    task_list = [l.split('：')[-1].strip() for l in user_input.split('\n') if l.strip()]
    
    if task_list:
        st.divider()
        st.subheader(f"📦 待处理任务: {len(task_list)} 条")
        
        # 生成并显示 JS
        final_js = generate_magic_code(task_list)
        st.code(final_js, language="javascript")
        
        st.info("💡 操作指引：点击上方代码框右上角复制，去目标站 F12 -> Console 粘贴回车。")
    else:
        st.error("⚠️ 框里没东西，生成个寂寞啊哥们！")

if st.button("🗑️ 清空全部内容"):
    st.session_state.auto_input_cache = ""
    st.rerun()
