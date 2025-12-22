import streamlit as st
import json
import urllib.parse

# --- 1. 配置 ---
st.set_page_config(layout="wide", page_title="Auto Task")

# --- 2. 核心：MagicPrompt v15.0 JS 模板 (你的原版逻辑) ---
def generate_magic_script(prompt_list):
    # 将提示词列表转为 JSON 并进行 URL 编码，防止特殊字符搞崩溃脚本
    encoded_data = urllib.parse.quote(json.dumps(prompt_list))
    
    # 这里嵌入你提供的顶级 JS 自动化逻辑
    js_template = f"""(async function() {{
    window.kill = false;
    const tasks = JSON.parse(decodeURIComponent("{encoded_data}"));
    
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

    showStatus("🚀 纹身自动化开始...");
    for (let i = 0; i < tasks.length; i++) {{
        if (window.kill) break;
        showStatus("✍️ 正在下单: " + (i+1) + "/" + tasks.length);
        let box = getInputBox();
        if (!box) {{ showStatus("❌ 找不到输入框", "#ef4444"); break; }}
        box.focus();
        document.execCommand('insertText', false, tasks[i]);
        await new Promise(r => setTimeout(r, 1000));
        box.dispatchEvent(new Event('input', {{ bubbles: true }}));
        let sendBtn = getSendBtn();
        if (sendBtn) sendBtn.click();
        
        // 智能等待逻辑
        if (i < tasks.length - 1) {{
            await new Promise(r => setTimeout(r, 3000));
            let waitTime = 0;
            while(isGenerating() && !window.kill) {{
                showStatus("🎨 AI 正在作画 (" + waitTime + "s)...", "#8b5cf6");
                await new Promise(r => setTimeout(r, 1000));
                waitTime++;
                if (waitTime > 180) break;
            }}
            showStatus("⏳ 冷却中...", "#f59e0b");
            await new Promise(r => setTimeout(r, 5000));
        }}
    }}
    showStatus("🎉 全部画完啦！", "#10b981");
}})();"""
    return js_template

# --- 3. UI 界面 ---
st.title("🤖 自动化任务分发中控")

# 检查上一模块传来的数据
# 这里我们要用到 session_state.polished_text (你在模块2保存的润色提示词)
raw_prompts = st.session_state.get('polished_text', "")

if not raw_prompts:
    st.warning("⚠️ 还没选好方案呢！请先去 [Creative] 页面勾选方案并点击【艺术润色】。")
else:
    # 自动切分方案
    # 假设 DeepSeek 输出的格式是 "方案1：... 方案2：..."
    # 我们按行切分出真正的提示词内容
    task_list = [line.split('：')[-1].strip() for line in raw_prompts.split('\n') if '：' in line or ':' in line]
    
    if not task_list: # 容错处理
        task_list = [line.strip() for line in raw_prompts.split('\n') if line.strip()]

    st.success(f"已就绪！共检测到 {len(task_list)} 条跑图任务。")

    with st.expander("📝 预览待下发指令", expanded=True):
        for i, task in enumerate(task_list):
            st.code(f"任务 {i+1}: {task}")

    # 生成脚本
    magic_code = generate_magic_script(task_list)

    st.divider()
    st.subheader("🚀 复制全能脚本 (F12)")
    
    # 重点：提供一键复制
    st.text_area("点击下方按钮复制此脚本，去目标网站控制台粘贴：", magic_code, height=300)
    
    st.info("""
    **使用说明：**
    1. 点击上方代码框全选并复制。
    2. 打开你想跑图的 AI 网站（Gemini / ChatGPT / 豆包等）。
    3. 按 **F12** 进入开发者工具，点击 **Console (控制台)**。
    4. 粘贴代码，按回车 **Enter**。
    5. 脚本会自动开始循环跑图，你只需要喝咖啡等着。
    """)
