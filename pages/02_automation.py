import streamlit as st
from style_manager import apply_pro_style

# 📍 傻瓜调用：全站视觉一键同步
apply_pro_style()

# --- 1. 新增组件库 (用于自动复制) ---
import streamlit.components.v1 as components
import json
import urllib.parse
import re

st.set_page_config(layout="wide", page_title="Automation Central")

# 📍 定位：外观装修区
st.markdown("""
<style>
    /* 1. 整体暗色背景 */
    .stApp { background-color: #0e1117; }

    /* 2. 平台选择下拉框美化 */
    div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }

    /* 3. 提示词文本框 - 磨砂黑色 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        color: #c9d1d9 !important;
        font-family: 'Consolas', 'Monaco', monospace;
    }

    /* 4. 操作步骤卡片 - 采用暗调处理 */
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }

    /* 5. 激发按钮 - 红色渐变呼吸灯感 */
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

# --- 核心 JS 模板 ---
def generate_v15_script(prompts, platform_type):
    encoded_data = urllib.parse.quote(json.dumps(prompts))
    
    selector_logic = ""
    if platform_type == "ChatGPT":
        selector_logic = "return document.querySelector('#prompt-textarea');"
    elif platform_type == "Doubao":
        selector_logic = "return document.querySelector('div[contenteditable=\"true\"]');"
    else: 
        selector_logic = "return document.querySelector('#prompt-textarea, div[contenteditable=\"true\"], textarea, .n-input__textarea-el, [placeholder*=\"输入\"], [placeholder*=\"提问\"]');"

    return f"""(async function() {{
    window.kill = false;
    const tasks = JSON.parse(decodeURIComponent("{encoded_data}"));
    
    function showStatus(text, color = "#6366f1") {{
        let el = document.getElementById('magic-status-bar') || document.createElement('div');
        el.id = 'magic-status-bar';
        el.style.cssText = `
            position: fixed; 
            top: 25px; 
            left: 50%; 
            transform: translateX(-50%); 
            z-index: 999999; 
            padding: 12px 28px; 
            border-radius: 50px; 
            font-family: 'Segoe UI', sans-serif; 
            font-size: 13px; 
            font-weight: 600; 
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #fff; 
            background: rgba(13, 17, 23, 0.85); 
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 75, 75, 0.4); 
            box-shadow: 0 0 20px rgba(255, 75, 75, 0.2), inset 0 0 10px rgba(255, 75, 75, 0.05);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        `;
        if(!document.getElementById('magic-status-bar')) document.body.appendChild(el);
        el.textContent = text;
    }}

    function getInputBox() {{ {selector_logic} }}

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

    showStatus("🤖 纹身大师 v15.0【{platform_type}】模式启动...");
    for (let i = 0; i < tasks.length; i++) {{
        if (window.kill) break;
        showStatus("✍️ 正在输入方案 " + (i+1) + " / " + tasks.length, "#3b82f6");
        let box = getInputBox();
        if (!box) {{ showStatus("❌ 找不到输入框 (请切换平台或点一下输入框)", "#ef4444"); break; }}
        
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
            showStatus("⏳ 冷却 5s...", "#f59e0b");
            await new Promise(r => setTimeout(r, 5000));
        }}
    }}
    showStatus("🎉 任务全部完成！", "#10b981");
}})();"""

# --- 2. 页面布局 ---
st.title("🤖 自动化任务分发中控")

# 平台选择器
col_opt1, col_opt2 = st.columns([2, 1])
with col_opt1:
    target_platform = st.selectbox(
        "选择目标 AI 平台", 
        ["万能自适应 (推荐)", "ChatGPT", "Doubao (豆包/镜像站)"],
        help="不同平台输入框构造不同，手动选择更精准"
    )

# 提示词区域
default_text = st.session_state.get('auto_input_cache', "")
user_input = st.text_area("检查待处理的提示词内容：", value=default_text, height=300)

if st.button("🚀 生成全能适配脚本 (生成即复制)", type="primary", use_container_width=True):
            # 1. 智能拆分逻辑 (保持原样)
            if "###" in user_input_auto:
                task_list = [t.strip() for t in user_input_auto.split("###") if len(t.strip()) > 2]
            else:
                blocks = re.split(r'\*\*方案.*?\*\*', user_input_auto)
                task_list = [b.strip().replace('* ', '').replace('\n', ' ') for b in blocks if len(b.strip()) > 5]

            if task_list:
                # 2. 生成 JS 脚本内容
                js_lines = ["const tasks = ["]
                for t in task_list:
                    clean_text = t.replace('\n', ' ').replace('"', '\\"').replace("'", "\\'")
                    js_lines.append(f'    "{clean_text}",')
                
                js_lines.extend([
                    "];",
                    "tasks.forEach((task, i) => {",
                    "    console.log(`Sending Task ${i+1}:`, task);",
                    "});",
                    "alert('脚本任务已就绪');"
                ])
                js_code = "\n".join(js_lines)
                
                # --- 🔴 核心修改：生成的同时，静默执行复制命令 🔴 ---
                import json
                import streamlit.components.v1 as components
                
                # 把代码转义成 JSON 字符串，防止 JS 语法错误
                js_val = json.dumps(js_code)
                
                # 插入一段高度为 0 的隐形 JS，负责干活
                components.html(f"""
                <script>
                    // 尝试写入剪贴板
                    navigator.clipboard.writeText({js_val}).then(function() {{
                        console.log('自动复制成功！');
                    }}, function(err) {{
                        console.error('自动复制失败，可能是浏览器拦截: ', err);
                    }});
                </script>
                """, height=0)
                # ---------------------------------------------------

                # 3. 界面反馈
                st.toast(f"✅ 已生成 {len(task_list)} 条任务，并已自动写入剪贴板！")
                st.success("脚本已复制！直接去浏览器 F12 粘贴即可。")
                
                # 4. 保底展示 (万一浏览器拦截了自动复制，还能手动拷)
                st.code(js_code, language="javascript")
            else:
                st.error("❌ 未识别到任务，请检查是否包含 ###")
