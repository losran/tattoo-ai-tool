import streamlit as st
from style_manager import apply_pro_style
import streamlit.components.v1 as components
import json
import urllib.parse
import re

# 1. 基础配置
st.set_page_config(layout="wide", page_title="Automation Central")
apply_pro_style()

# 2. 样式注入
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        font-family: 'Consolas', 'Monaco', monospace;
    }
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #d62f2f 100%) !important;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2) !important;
        border: none !important;
        height: 50px !important;
        font-size: 18px !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 页面标题
st.title("🤖 自动化任务分发中控")

# 4. 平台选择
col_opt1, col_opt2 = st.columns([2, 1])
with col_opt1:
    target_platform = st.selectbox(
        "选择目标 AI 平台", 
        ["万能自适应 (推荐)", "ChatGPT", "Doubao (豆包/镜像站)"],
        help="不同平台输入框构造不同，手动选择更精准"
    )

# 5. 输入区域
default_text = st.session_state.get('auto_input_cache', "")
if not default_text:
    default_text = st.session_state.get('polished_text', "")

user_input = st.text_area("检查待处理的提示词内容：", value=default_text, height=300, key="main_input_area")

# --- 🟢 新增功能区：生产辅助选项 ---
st.divider()
col_check, col_btn = st.columns([1, 2])
with col_check:
    # ✨ 这里是新加的开关 ✨
    need_white_bg = st.checkbox("🏭 生产模式：每张图后自动生成白底图", value=False, help="勾选后，会在每个方案后面自动插入一条'生成上图白底图'的指令，方便扣图生产。")

# 6. 生成按钮逻辑
with col_btn:
    if st.button("🚀 生成全能适配脚本 (v15.0 防卡死版)", type="primary", use_container_width=True):
        # --- A. 智能拆分任务 ---
        task_list = []
        if user_input:
            if "###" in user_input:
                raw_tasks = [t.strip() for t in user_input.split("###") if len(t.strip()) > 2]
            else:
                blocks = re.split(r'\*\*方案[一二三四五六七八九十\d]+[:：].*?\*\*', user_input)
                raw_tasks = [b.strip().replace('* ', '').replace('\n', ' ') for b in blocks if len(b.strip()) > 5]
            
            # --- 🟢 核心逻辑：自动插入“白底图”指令 ---
            if need_white_bg:
                for t in raw_tasks:
                    task_list.append(t)  # 先放方案
                    task_list.append("生成上图白底图")  # 紧接着放白底图指令
            else:
                task_list = raw_tasks # 否则就原样输出

        # --- B. 生成脚本 ---
        if task_list:
            encoded_data = urllib.parse.quote(json.dumps(task_list))

            # JS 核心代码 (v15.0 内核)
            js_code = f"""(async function() {{
                window.kill = false;
                const tasks = JSON.parse(decodeURIComponent("{encoded_data}"));

                // 1. UI 状态条
                function showStatus(text, color = "#1e293b", textColor = "#fff") {{
                    let el = document.getElementById('magic-status-bar');
                    if (!el) {{
                        el = document.createElement('div');
                        el.id = 'magic-status-bar';
                        el.style.cssText = "position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:999999; padding:10px 20px; border-radius:30px; font-family:sans-serif; font-size:14px; font-weight:bold; box-shadow:0 10px 25px rgba(0,0,0,0.2); transition: all 0.3s;";
                        document.body.appendChild(el);
                    }}
                    el.textContent = text;
                    el.style.backgroundColor = color;
                    el.style.color = textColor;
                }}

                // 2. 输入框探测
                function getInputBox() {{
                    return document.querySelector(
                        '#prompt-textarea, div[contenteditable="true"], textarea, .n-input__textarea-el, [placeholder*="输入"], [placeholder*="提问"]'
                    );
                }}

                // 3. 发送按钮探测
                function getSendBtn() {{
                    let btns = Array.from(document.querySelectorAll('button, [role="button"], i'));
                    return btns.find(b => {{
                        const t = (b.innerText || b.ariaLabel || b.className || "").toLowerCase();
                        const isSend = t.includes('发') || t.includes('send') || (b.tagName === 'I' && t.includes('send')) || b.getAttribute('data-testid') === 'send-button';
                        const isNew = t.includes('新') || t.includes('new');
                        const isStop = t.includes('stop') || t.includes('停止');
                        return isSend && !isNew && !isStop && b.offsetParent !== null && !b.disabled;
                    }});
                }}

                // 4. 生成状态探测
                function isGenerating() {{
                    let btns = Array.from(document.querySelectorAll('button, [role="button"]'));
                    return btns.some(b => {{
                        const t = (b.innerText || b.ariaLabel || "").toLowerCase();
                        return t.includes('stop') || t.includes('停止') || t.includes('generating');
                    }});
                }}

                console.log("%c🤖 v15.0 启动", "color:#6366f1; font-weight:bold;");
                showStatus("🚀 脚本就绪...", "#6366f1");

                for (let i = 0; i < tasks.length; i++) {{
                    if (window.kill) {{ showStatus("🛑 已停止", "#ef4444"); break; }}
                    
                    showStatus("✍️ 输入: " + (i+1) + "/" + tasks.length, "#3b82f6");
                    let box = getInputBox();
                    if (!box) {{ showStatus("❌ 找不到输入框", "#ef4444"); break; }}
                    
                    box.focus();
                    document.execCommand('insertText', false, tasks[i]);
                    await new Promise(r => setTimeout(r, 1000));
                    box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    await new Promise(r => setTimeout(r, 500));
                    box.dispatchEvent(new KeyboardEvent('keydown', {{bubbles:true, cancelable:true, key:'Enter', code:'Enter', keyCode:13}}));

                    let sendBtn = getSendBtn();
                    if (sendBtn) sendBtn.click();
                    
                    if (i < tasks.length - 1) {{
                        let waitTime = 0;
                        await new Promise(r => setTimeout(r, 3000));
                        while(true) {{
                            if (window.kill) break;
                            if (!isGenerating()) break;
                            
                            showStatus("🎨 作画中 (" + waitTime + "s)...", "#8b5cf6");
                            await new Promise(r => setTimeout(r, 1000));
                            waitTime++;
                            if (waitTime > 180) break;
                        }}
                        for (let s = 5; s > 0; s--) {{
                            if (window.kill) break;
                            showStatus("⏳ 冷却: " + s + "s", "#f59e0b");
                            await new Promise(r => setTimeout(r, 1000));
                        }}
                    }}
                }}
                if(!window.kill) {{
                    showStatus("🎉 全部完成！", "#10b981");
                    setTimeout(() => document.getElementById('magic-status-bar').remove(), 5000);
                }}
            }})();"""

            # --- C. 自动复制 ---
            js_val = json.dumps(js_code)
            components.html(f"""
            <script>
                const text = {js_val};
                if (navigator.clipboard) {{
                    navigator.clipboard.writeText(text).catch(err => console.log('Auto-copy failed'));
                }}
            </script>
            """, height=0)

            # --- D. 界面反馈 ---
            st.success(f"✅ 已生成 {len(task_list)} 条任务指令！")
            if need_white_bg:
                st.info("💡 已开启生产模式：每张图后面都插入了“生成上图白底图”指令。")
            
            st.caption("👇 如果自动复制失败，请点击代码框右上角的【📄】按钮：")
            st.code(js_code, language="javascript")
            
        else:
            st.error("❌ 未识别到任务内容，请确保文本框有内容且包含 '**方案...**' 或 '###'")

# 7. 清空按钮
if st.button("🗑️ 清空当前任务"):
    st.session_state.auto_input_cache = ""
    st.session_state.polished_text = ""
    st.rerun()
