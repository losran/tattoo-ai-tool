// --- 替换 pages/02_automation.py 里的 js_code 变量内容 ---
js_code = f"""(async function() {{
    window.kill = false;
    window.onbeforeunload = null; // 暴力防止跳转拦截
    
    const tasks = JSON.parse(decodeURIComponent("{encoded_data}"));
    
    function showStatus(text, color = "#6366f1") {{
        let el = document.getElementById('magic-status-bar') || document.createElement('div');
        if (!el.id) {{
            el.id = 'magic-status-bar';
            el.style.cssText = "position:fixed; top:20px; left:50%; transform:translateX(-50%); z-index:9999999; padding:12px 24px; border-radius:30px; font-family:sans-serif; font-size:14px; font-weight:bold; color:#fff; box-shadow:0 10px 25px rgba(0,0,0,0.5); pointer-events:none;";
            document.body.appendChild(el);
        }}
        el.textContent = text;
        el.style.backgroundColor = color;
    }}

    function getInputBox() {{
        // 增加更多备用选择器
        return document.querySelector('#prompt-textarea, [contenteditable="true"], textarea, .n-input__textarea-el, .ProseMirror');
    }}

    async function forceInput(box, text) {{
        box.focus();
        // 绕过 React/Vue 拦截的核心逻辑
        const elementPrototype = window.HTMLElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set 
                      || Object.getOwnPropertyDescriptor(elementPrototype, "innerText")?.set 
                      || Object.getOwnPropertyDescriptor(elementPrototype, "innerHTML")?.set;
        
        if (setter) {{
            setter.call(box, text);
        }} else {{
            box.value = text;
            box.innerText = text;
        }}
        
        // 触发一组标准事件流，确保“发送按钮”变亮
        const events = ['input', 'change', 'blur'];
        events.forEach(name => box.dispatchEvent(new Event(name, {{ bubbles: true, cancelable: true }})));
    }}

    showStatus("🚀 脚本启动 (v17.0 静默版)", "#6366f1");

    for (let i = 0; i < tasks.length; i++) {{
        if (window.kill) break;
        
        showStatus(`✍️ 录入中: ${{i+1}}/${{tasks.length}}`, "#3b82f6");
        let box = getInputBox();
        if (!box) {{ showStatus("❌ 找不到输入框", "#ef4444"); break; }}

        // 1. 深度录入文字
        await forceInput(box, tasks[i]);
        await new Promise(r => setTimeout(r, 1200)); // 增加稳定等待

        // 2. 查找发送按钮（精确匹配）
        let sendBtn = null;
        const allBtns = Array.from(document.querySelectorAll('button, [role="button"]'));
        sendBtn = allBtns.find(b => {{
            const style = window.getComputedStyle(b);
            if (style.display === 'none' || style.visibility === 'hidden') return false;
            const text = (b.innerText || b.getAttribute('aria-label') || "").toLowerCase();
            return (text.includes('发') || text.includes('send') || b.querySelector('svg')) && !b.disabled;
        }});

        // 3. 模拟点击并防止路由触发
        if (sendBtn) {{
            sendBtn.focus();
            sendBtn.click();
        }} else {{
            // 回车兜底
            box.dispatchEvent(new KeyboardEvent('keydown', {{bubbles:true, key:'Enter', code:'Enter', keyCode:13, which:13}}));
        }}

        // 4. 等待生成逻辑（防止连发）
        await new Promise(r => setTimeout(r, 3000));
        let waitTime = 0;
        while (!window.kill) {{
            // 实时探测是否有“停止”或“正在生成”的标志
            const isActive = Array.from(document.querySelectorAll('button, div')).some(el => {{
                const t = (el.innerText || el.getAttribute('aria-label') || "").toLowerCase();
                return t.includes('stop') || t.includes('停止') || t.includes('cancel');
            }});
            
            if (!isActive) break;
            showStatus(`🎨 AI 作画中 (${{waitTime}}s)...`, "#8b5cf6");
            await new Promise(r => setTimeout(r, 1000));
            if (waitTime++ > 150) break; // 超时跳出
        }}

        // 5. 任务间隔冷却
        if (i < tasks.length - 1) {{
            for (let s = 4; s > 0; s--) {{
                if (window.kill) break;
                showStatus(`⏳ 冷却: ${{s}}s`, "#f59e0b");
                await new Promise(r => setTimeout(r, 1000));
            }}
        }}
    }}
    showStatus("🎉 全部完成！", "#10b981");
    setTimeout(() => document.getElementById('magic-status-bar')?.remove(), 5000);
}})();"""
