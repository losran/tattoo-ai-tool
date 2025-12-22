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
if st.button("🚀 生成全能适配脚本 (v15.0 防卡死版)", type="primary", use_container_width=True):
    # 1. 智能拆分逻辑 (优先 ###)
    if "###" in user_input:
        task_list = [t.strip() for t in user_input.split("###") if len(t.strip()) > 2]
    else:
        blocks = re.split(r'\*\*方案[一二三四五六七八九十\d]+[:：].*?\*\*', user_input)
        task_list = [b.strip().replace('* ', '').replace('\n', ' ') for b in blocks if len(b.strip()) > 5]

    if task_list:
        import urllib.parse
        import json
        
        # 2. 数据编码：把 Python 列表转为 JS 安全的字符串
        encoded_data = urllib.parse.quote(json.dumps(task_list))

        # 3. 核心 JS 逻辑移植 (v15.0 Anti-Freeze)
        # 这段代码就是你 HTML 里的核心逻辑，已经完美移植到 Python 字符串中
        js_code = f"""(async function() {{
            window.kill = false;
            const tasks = JSON.parse(decodeURIComponent("{encoded_data}"));

            // UI 进度条
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

            // 全能输入框探测器 (含 ChatGPT / Doubao / 镜像站)
            function getInputBox() {{
                return document.querySelector(
                    '#prompt-textarea, ' + // ChatGPT
                    'div[contenteditable="true"], ' + // 通用 & Doubao
                    'textarea, ' + 
                    '.n-input__textarea-el, ' + // Node6
                    '[placeholder*="输入"], [placeholder*="提问"]'
                );
            }}

            // 全能发送按钮探测器
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

            // 探测是否正在生成 (是否有停止按钮)
            function isGenerating() {{
                let btns = Array.from(document.querySelectorAll('button, [role="button"]'));
                return btns.some(b => {{
                    const t = (b.innerText || b.ariaLabel || "").toLowerCase();
                    return t.includes('stop') || t.includes('停止') || t.includes('generating');
                }});
            }}

            console.log("%c🤖 全能模式启动 | 适配 ChatGPT/Doubao/Mirror", "color:#6366f1; font-weight:bold;");
            showStatus("🚀 脚本就绪，开始执行...", "#6366f1");

            for (let i = 0; i < tasks.length; i++) {{
                if (window.kill) {{ showStatus("🛑 已停止", "#ef4444"); break; }}
                
                showStatus("✍️ 正在输入: " + (i+1) + " / " + tasks.length, "#3b82f6");
                let box = getInputBox();
                
                if (!box) {{ 
                    console.error("未找到输入框"); 
                    showStatus("❌ 找不到输入框 (请手动点击一下)", "#ef4444");
                    break; 
                }}

                box.focus();
                document.execCommand('insertText', false, tasks[i]);
                await new Promise(r => setTimeout(r, 1000));

                // 尝试触发 input 事件 (适配 React/Vue 网站)
                box.dispatchEvent(new Event('input', {{ bubbles: true }}));
                await new Promise(r => setTimeout(r, 500));
                
                // 模拟回车
                box.dispatchEvent(new KeyboardEvent('keydown', {{bubbles:true, cancelable:true, key:'Enter', code:'Enter', keyCode:13}}));

                // 点击发送 (双重保险)
                let sendBtn = getSendBtn();
                if (sendBtn) sendBtn.click();
                
                console.log("✅ [" + (i+1) + "] 已尝试发送，进入监控...");

                // 智能等待 (防卡死核心)
                if (i < tasks.length - 1) {{
                    let waitTime = 0;
                    // 先给 3 秒让“停止”按钮出来
                    await new Promise(r => setTimeout(r, 3000));

                    while(true) {{
                        if (window.kill) break;
                        
                        // 核心判断：如果看不到“停止”按钮，就认为画完了！
                        if (!isGenerating()) {{
                            break;
                        }}

                        showStatus("🎨 AI 正在作画 (" + waitTime + "s)...", "#8b5cf6");
                        await new Promise(r => setTimeout(r, 1000));
                        waitTime++;
                        
                        if (waitTime > 180) break;
                    }}

                    // 冷却倒计时 5s
                    for (let s = 5; s > 0; s--) {{
                        if (window.kill) break;
                        showStatus("⏳ 冷却中: " + s + "s", "#f59e0b");
                        await new Promise(r => setTimeout(r, 1000));
                    }}
                }}
            }}
            
            if(!window.kill) {{
                showStatus("🎉 任务全部完成！", "#10b981");
                setTimeout(() => document.getElementById('magic-status-bar').remove(), 5000);
            }}
        }})();"""

        # 4. 自动复制逻辑 (将上面的 js_code 写入剪贴板)
        js_val = json.dumps(js_code)
        components.html(f"""
        <script>
            navigator.clipboard.writeText({js_val}).then(function() {{
                console.log('v15.0 脚本自动复制成功');
            }}, function(err) {{
                console.error('自动复制失败: ', err);
            }});
        </script>
        """, height=0)

        # 5. 界面反馈
        st.toast(f"✅ 已生成 {len(task_list)} 条任务，v15.0 脚本已写入剪贴板！")
        st.success("🎉 脚本已升级为 v15.0 防卡死版！直接去浏览器 F12 粘贴即可。")
        st.info("💡 新特性：自动监控「停止」按钮，画完自动发下一张，支持 ChatGPT/豆包/镜像站。")
        
        # 6. 保底展示
        st.code(js_code, language="javascript")
    else:
        st.error("❌ 未识别到任务，请检查是否包含 ###")
