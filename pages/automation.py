import streamlit as st
import json
import urllib.parse

# --- 1. 页面配置 ---
st.set_page_config(layout="wide", page_title="Auto Task Central")

# --- 2. 核心：JS 脚本生成器 (基于你的 MagicPrompt v15.0) ---
def generate_js_code(prompts):
    # 将列表转为 JSON 并进行编码，确保特殊字符不会破坏 JS 语法
    encoded_prompts = urllib.parse.quote(json.dumps(prompts))
    
    # 这里是你那段“全平台制霸”的 JS 逻辑
    js_template = f"""(async function() {{
    window.kill = false;
    const tasks = JSON.parse(decodeURIComponent("{encoded_prompts}"));
    
    function showStatus(text, color = "#6366f1") {{
        let el = document.getElementById('magic-status-bar');
        if (!el) {{
            el = document.createElement('div');
            el.id = 'magic-status-bar';
            el.style.cssText = "position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:999999; padding:10px 20px; border-radius:30px; font-family:sans-serif; font-size:14px; font-weight:bold; box-shadow:0 10px 25px rgba(0,0,0,0.2); transition: all 0.3s;";
            document.body.appendChild(el);
        }}
        el.textContent = text; el.style.backgroundColor = color; el.style.color = "#fff";
    }}

    function getInputBox() {{
        return document.querySelector('#prompt-textarea, div[contenteditable="true"], textarea, .n-input__textarea-el, [placeholder*="输入"], [placeholder*="提问"]');
    }}

    function getSendBtn() {{
        let btns = Array.from(document.querySelectorAll('button, [role="button"], i'));
        return btns.find(b => {{
            const t = (b.innerText || b.ariaLabel || b.className || "").toLowerCase();
            const isSend = t.includes('发') || t.includes('send') || (b.tagName === 'I' && t.includes('send')) || b.getAttribute('data-testid') === 'send-button';
            return isSend && !t.includes('新') && !t.includes('stop') && b.offsetParent !== null && !b.disabled;
        }});
    }}

    function isGenerating() {{
        let btns = Array.from(document.querySelectorAll('button, [role="button"]'));
        return btns.some(b => {{
            const t = (b.innerText || b.ariaLabel || "").toLowerCase();
            return t.includes('stop') || t.includes('停止') || t.includes('generating');
        }});
    }}

    showStatus("🚀 自动化流程启动...");
    for (let i = 0; i < tasks.length; i++) {{
        if (window.kill) break;
        showStatus("✍️ 正在执行任务: " + (i+1) + " / " + tasks.length);
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
                if (waitTime > 240) break;
            }}
            showStatus("⏳ 冷却中 (5s)...", "#f59e0b");
            await new Promise(r => setTimeout(r, 5000));
        }}
    }}
    showStatus("🎉 任务全部完成！", "#10b981");
}})();"""
    return js_template

# --- 3. UI 布局 ---
st.title("🤖 自动化任务中控")

# 检查是否有来自第二模块的润色成果
from_creative = st.session_state.get('polished_text', "")

# 顶部分块选择
tab1, tab2 = st.tabs(["⚡ 快捷导入 (从创意引擎)", "✍️ 手动粘贴 (外部搬运)"])

with tab1:
    if from_creative:
        st.success("✅ 检测到已生成的润色方案！")
        st.text_area("内容预览：", from_creative, height=150, disabled=True)
        if st.button("🚀 导入并生成自动化脚本", type="primary", key="import_btn"):
            # 解析提示词：按行切分并清洗
            lines = [l.strip() for l in from_creative.split('\n') if l.strip()]
            # 过滤掉“方案1：”这种前缀，只留内容
            clean_prompts = [l.split('：')[-1].split(':')[-1] for l in lines]
            st.session_state.final_task_list = clean_prompts
    else:
        st.info("目前没有润色好的方案，请先去 [Creative] 页面完成润色。")

with tab2:
    manual_input = st.text_area("请粘贴提示词（每行一条）：", height=200, placeholder="提示词1\n提示词2\n...")
    if st.button("🛠️ 生成手动任务脚本"):
        lines = [l.strip() for l in manual_input.split('\n') if l.strip()]
        st.session_state.final_task_list = lines

# --- 4. 脚本分发区 ---
if 'final_task_list' in st.session_state and st.session_state.final_task_list:
    st.divider()
    st.subheader(f"📦 待处理任务 ({len(st.session_state.final_task_list)} 条)")
    
    with st.expander("查看任务明细"):
        for i, p in enumerate(st.session_state.final_task_list):
            st.write(f"{i+1}. {p}")
            
    # 生成最终 JS
    final_js = generate_js_code(st.session_state.final_task_list)
    
    st.info("👇 点击下方按钮复制代码，然后在跑图网站(ChatGPT/豆包)按 F12 粘贴回车")
    st.code(final_js, language="javascript")
    
    if st.button("🗑️ 清空当前任务流"):
        st.session_state.final_task_list = []
        st.rerun()
