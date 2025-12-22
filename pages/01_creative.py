import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt", "Action": "data/actions.txt", 
    "Style": "data/styles.txt", "Mood": "data/moods.txt", "Usage": "data/usage.txt"
}
GALLERY_FILE = "gallery/inspirations.txt"

# --- 2. 工具函数 ---
def get_github_data(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    except: pass
    return []

def save_to_github(path, data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        get_resp = requests.get(url, headers=headers, timeout=10).json()
        content_str = "\n".join(list(set(data_list)))
        b64_content = base64.b64encode(content_str.encode()).decode()
        requests.put(url, headers=headers, json={"message": "update", "content": b64_content, "sha": get_resp.get('sha')}, timeout=15)
        return True
    except: return False

# --- 3. UI 布局与状态初始化 ---
st.title("🎨 创意引擎")

# 初始化所有关键状态
for key in ['selected_prompts', 'generated_cache', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

col_main, col_gallery = st.columns([5, 2.5])

# --- 右侧：仓库管理 (支持批量删除与导入) ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    
    if mode == "素材仓库":
        cat = st.selectbox("当前分类", list(WAREHOUSE.keys()))
        words = get_github_data(WAREHOUSE[cat])
        
        if words:
            selected_items = []
            st.caption(f"共 {len(words)} 个标签。请勾选进行操作：")
            with st.container(height=500, border=True):
                for w in words:
                    if st.checkbox(f" {w}", key=f"manage_{cat}_{w}"):
                        selected_items.append(w)
            
            if selected_items:
                st.divider()
                # 📍 功能：导入到输入框
                if st.button("➕ 导入到组合输入框", use_container_width=True):
                    existing = st.session_state.manual_editor
                    new_text = " ".join(selected_items)
                    st.session_state.manual_editor = f"{existing} {new_text}".strip()
                    st.rerun()
                
                # 功能：批量删除
                if st.button(f"🗑️ 删除选中的 {len(selected_items)} 项", type="primary", use_container_width=True):
                    remaining = [w for w in words if w not in selected_items]
                    if save_to_github(WAREHOUSE[cat], remaining):
                        st.success("清理成功")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("暂无数据")
    else:
        insps = get_github_data(GALLERY_FILE)
        # ... 灵感成品管理逻辑保持一致 ...
        if insps:
            sel_insps = []
            with st.container(height=500, border=True):
                for i in insps:
                    if st.checkbox(i, key=f"del_i_{hash(i)}"): sel_insps.append(i)
            if sel_insps and st.button("🗑️ 删除勾选灵感", type="primary"):
                remaining = [i for i in insps if i not in sel_insps]
                save_to_github(GALLERY_FILE, remaining); st.rerun()

# --- 左侧：核心生成区 ---
with col_main:
    # 📍 调整 1：组合输入框 (放在最前面)
    st.subheader("📝 灵感调配区")
    st.session_state.manual_editor = st.text_area(
        "手动编辑或从右侧导入关键词：", 
        value=st.session_state.manual_editor,
        placeholder="例如：黑灰写实 龙 牡丹... (空格分隔)",
        height=100
    )

    # 📍 调整 2：混乱参数 (创意程度)
    st.divider()
    chaos_level = st.slider(
        "✨ 创意混乱参数 (Chaos Level)", 
        min_value=0, max_value=100, value=50, 
        help="0: 严格遵守输入词 | 50: 适度联想仓库词 | 100: 凭空脑补、放飞自我"
    )

    # 调整 3：生成数量
    col_num1, col_num2 = st.columns([1, 2])
    with col_num1:
        num = st.number_input("生成数量", min_value=1, max_value=15, value=3)
    with col_num2:
        st.caption("快捷设置")
        q_cols = st.columns(3)
        if q_cols[0].button("3"): st.session_state.gen_n = 3
        if q_cols[1].button("5"): st.session_state.gen_n = 5
        if q_cols[2].button("10"): st.session_state.gen_n = 10
        if 'gen_n' in st.session_state:
            num = st.session_state.gen_n
            del st.session_state.gen_n

    if st.button("🔥 激发创意生成", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        # 📍 核心生成逻辑：根据混乱参数调整权重
        for _ in range(num):
            final_elements = []
            
            # 1. 基础词来源于输入框
            manual_words = st.session_state.manual_editor.split()
            
            # 2. 混乱度判定
            # 混乱度越高，从仓库随机抽取的词越多，或者甚至跳出框架
            if chaos_level < 30:
                # 低混乱：只用手动词 + 1个仓库补位
                final_elements = manual_words + [random.choice(db_all[random.choice(list(db_all.keys()))]) if any(db_all.values()) else ""]
            elif chaos_level <= 70:
                # 中混乱：手动词 + 随机3个维度词
                extra = [random.choice(db_all[c]) for c in random.sample(list(db_all.keys()), 3) if db_all.get(c)]
                final_elements = manual_words + extra
            else:
                # 高混乱：手动词仅作为背景，大量随机或脑补
                extra = [random.choice(db_all[c]) for c in list(db_all.keys()) if db_all.get(c)]
                final_elements = manual_words + extra + ["（自由发挥极致创意）"]
            
            st.session_state.generated_cache.append(" + ".join(filter(None, final_elements)))
        st.rerun()

    # --- 方案展示 ---
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 方案筛选")
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**组合 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(p)
                    if st.button("选中" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(p)
                        else: st.session_state.selected_prompts.append(p)
                        st.rerun()

    # --- 润色区 ---
    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("正在根据混乱参数微调文案..."):
                combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                # 将混乱参数传给 AI
                system_instruction = f"你是一个纹身艺术顾问。将标签转化为中文提示词。当前混乱等级为{chaos_level}/100（越接近100越需要脑补和抽象，越接近0越要忠于原词）。格式：'**方案X：** 内容'。"
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": combined}]
                ).choices[0].message.content
                st.session_state.polished_text = res

    # --- 成果与传送 ---
    if st.session_state.get('polished_text'):
        st.success("✅ 润色完成")
        final_content = st.text_area("最终成果：", st.session_state.polished_text, height=250)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 存入灵感成品库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                new = [l.strip() for l in final_content.split('\n') if l.strip() and '方案' not in l]
                current.extend(new)
                save_to_github(GALLERY_FILE, current); st.success("已存入成品库")
        with c2:
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
