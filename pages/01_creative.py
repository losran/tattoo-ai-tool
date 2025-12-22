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

for key in ['selected_prompts', 'generated_cache', 'polished_text']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

col_main, col_gallery = st.columns([5, 2.5]) # 稍微加宽一点管理区

# --- 右侧：仓库管理 (列表勾选删除模式) ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("切换预览", ["素材仓库", "灵感成品"], horizontal=True)
    
    if mode == "素材仓库":
        cat = st.selectbox("当前分类", list(WAREHOUSE.keys()))
        words = get_github_data(WAREHOUSE[cat])
        
        if words:
            st.caption(f"共 {len(words)} 个标签。勾选想要清理的项：")
            selected_to_delete = []
            with st.container(height=500, border=True):
                for w in words:
                    if st.checkbox(f" {w}", key=f"del_{cat}_{w}"):
                        selected_to_delete.append(w)
            
            if selected_to_delete:
                st.divider()
                st.error(f"已选中 {len(selected_to_delete)} 个标签")
                if st.button("🗑️ 确认批量删除所选", type="primary", use_container_width=True):
                    remaining = [w for w in words if w not in selected_to_delete]
                    if save_to_github(WAREHOUSE[cat], remaining):
                        st.success("清理完成！")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("分类下暂无素材")
            
    else:
        insps = get_github_data(GALLERY_FILE)
        if insps:
            selected_insps = []
            with st.container(height=500, border=True):
                for i in insps:
                    if st.checkbox(i, key=f"del_insp_{hash(i)}"):
                        selected_insps.append(i)
            if selected_insps:
                st.divider()
                if st.button(f"🗑️ 批量删除灵感 ({len(selected_insps)})", type="primary", use_container_width=True):
                    remaining_insp = [i for i in insps if i not in selected_insps]
                    save_to_github(GALLERY_FILE, remaining_insp)
                    st.rerun()
        else:
            st.caption("灵感库为空")

# --- 左侧：核心生成区 ---
with col_main:
    # 📍 优化点 1：生成数量 UI 改造
    st.subheader("🔥 方案生成")
    col_num1, col_num2 = st.columns([1, 2])
    with col_num1:
        num = st.number_input("一次生成几条？", min_value=1, max_value=20, value=3, step=1)
    with col_num2:
        st.caption("快捷选择")
        quick_cols = st.columns(3)
        if quick_cols[0].button("3条"): st.session_state['gen_count'] = 3
        if quick_cols[1].button("5条"): st.session_state['gen_count'] = 5
        if quick_cols[2].button("10条"): st.session_state['gen_count'] = 10
        # 如果点了快捷按钮，更新输入框的值
        if 'gen_count' in st.session_state:
            num = st.session_state['gen_count']
            del st.session_state['gen_count']

    if st.button("🔥 开始随机组合", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        if not any(db_all.values()):
            st.error("素材库是空的！")
        else:
            for _ in range(num):
                sample = [random.choice(db_all[cat]) if db_all.get(cat) else " " for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
                st.session_state.generated_cache.append(" + ".join(sample))
            st.rerun()

    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 随机组合结果")
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**组合 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(prompt)
                    if st.button("选择" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(prompt)
                        else: st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色 (针对已选组合)", type="primary", use_container_width=True):
            with st.spinner("正在构思文案..."):
                combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                system_prompt = "你是一个顶级纹身顾问。将标签转化为优美的中文提示词。严格按照'**方案X：** 内容'格式输出。"
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined}]
                ).choices[0].message.content
                st.session_state.polished_text = res

    # 📍 优化点 2：消除保存歧义
    if st.session_state.get('polished_text'):
        st.divider()
        st.subheader("🎨 艺术润色成果")
        final_content = st.text_area("润色完成的成品文案：", st.session_state.polished_text, height=250)
        
        c1, c2 = st.columns(2)
        with c1:
            # 明确按钮文案：存的是“润色成品”
            if st.button("💾 将润色成品存入灵感库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                new_lines = [l.strip() for l in final_content.split('\n') if l.strip() and '方案' not in l]
                current.extend(new_lines)
                if save_to_github(GALLERY_FILE, current):
                    st.balloons()
                    st.success("成品已永久存入 inspirations.txt")
        
        with c2:
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
