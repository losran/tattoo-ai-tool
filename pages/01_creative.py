import streamlit as st
import json
import os
import random
import numpy as np
import requests
import base64
from openai import OpenAI
from style_manager import apply_pro_style

# 📍 视觉样式同步
apply_pro_style()

# --- 1. 核心配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt", 
    "Action": "data/actions.txt", 
    "Style": "data/styles.txt", 
    "Mood": "data/moods.txt", 
    "Usage": "data/usage.txt"
}
GALLERY_FILE = "gallery/inspirations.txt"

# --- 2. 核心函数 ---
def smart_sample_with_ai(category, user_intent, inventory):
    if not user_intent or not user_intent.strip():
        return random.choice(inventory) if inventory else "空"
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：选一个词。只返回词汇。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        return res.choices[0].message.content.strip()
    except: return random.choice(inventory)

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

# --- 3. UI 布局与 Session 初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

for key in ['selected_prompts', 'history_workbench', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if 'editor' in key or 'text' in key else []

# 🔒 定义全局锁定状态 (缩进为 0)
is_working = len(st.session_state.polished_text) > 0

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 右侧：仓库管理 ---
# --- 右侧：仓库管理 (上) + 历史记录 (下) ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    
    # 1. 仓库管理容器 (素材/成品切换)
    with st.container(height=300, border=True):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            if words:
                for w in words:
                    if st.checkbox(f" {w}", key=f"cat_{cat}_{w}", disabled=is_working):
                        if not is_working and w not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(w)
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps:
                    if st.checkbox(i, key=f"insp_lib_{abs(hash(i))}", disabled=is_working):
                        if not is_working and i not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(i)

# --- 📜 激发历史区 (位于仓库下方) ---
    st.divider()
    st.subheader("📜 历史档案")
    if st.session_state.history_log:
        with st.container(height=400, border=True):
            for h_idx, h_text in enumerate(st.session_state.history_log):
                # 如果历史记录在已选中列表里，就勾选它
                is_selected = h_text in st.session_state.selected_prompts
                if st.checkbox(f"历史 {len(st.session_state.history_log)-h_idx}: {h_text}", 
                               key=f"h_log_{h_idx}_{abs(hash(h_text))}", 
                               value=is_selected,
                               disabled=is_working):
                    if not is_working:
                        if h_text not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(h_text)
                        st.rerun()
        
        if st.button("🗑️ 清空所有历史", use_container_width=True, disabled=is_working):
            st.session_state.history_log = []
            st.rerun()
    else:
        st.caption("暂无历史记录")

# --- 左侧：核心生成区 ---
with col_main:
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1: num = st.slider("生成方案数量", 1, 10, 6)
    with col_cfg2: chaos_level = st.slider("🎨 审美光谱：🌸 可爱 — 🐉 日式 — 📐 欧美极简", 0, 100, 55)
    
    intent_input = st.text_area("✍️ 组合意图输入框", value=st.session_state.manual_editor, disabled=is_working)
    st.session_state.manual_editor = intent_input

if st.button("🔥 激发创意组合", type="primary", use_container_width=True, disabled=is_working):
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        with st.spinner("AI 精准挑词中..."):
            new_batch = []
            for _ in range(num):
                s = smart_sample_with_ai("Subject", intent_input, db_all["Subject"])
                a = smart_sample_with_ai("Action", intent_input, db_all["Action"])
                st_val = smart_sample_with_ai("Style", intent_input, db_all["Style"])
                m = smart_sample_with_ai("Mood", intent_input, db_all["Mood"])
                u = smart_sample_with_ai("Usage", intent_input, db_all["Usage"])
                new_batch.append(f"{s}，{a}，{st_val}风格，{m}氛围，纹在{u}")
            
            # 💡 核心：只更新中间，历史区保持不动
            st.session_state.generated_cache = new_batch 
        st.rerun()

    # 3. 🎲 历史方案筛选 (带锁定逻辑)
    if st.session_state.history_workbench:
        st.divider()
        st.subheader(f"🎲 历史记录台")
        with st.container(height=400):
            cols = st.columns(2)
            for idx, p in enumerate(st.session_state.history_workbench):
                with cols[idx % 2]:
                    is_sel = p in st.session_state.selected_prompts
                    if st.button(f"{idx+1}. {p}", key=f"hist_{idx}_{abs(hash(p))}", 
                                 type="primary" if is_sel else "secondary", 
                                 disabled=is_working):
                        if not is_working:
                            if is_sel: st.session_state.selected_prompts.remove(p)
                            else: st.session_state.selected_prompts.append(p)
                            st.rerun()
        
        c_tool1, c_tool2 = st.columns(2)
        with c_tool1:
            if st.button("💾 存入成品库", use_container_width=True, disabled=is_working):
                if st.session_state.selected_prompts:
                    current = get_github_data(GALLERY_FILE)
                    current.extend(st.session_state.selected_prompts)
                    save_to_github(GALLERY_FILE, current); st.success("已存档")
        with c_tool2:
            if st.button("🗑️ 清除所有", use_container_width=True, disabled=is_working):
                st.session_state.history_workbench = []; st.session_state.selected_prompts = []; st.session_state.polished_text = ""
                st.rerun()

    # 4. ✨ 润色逻辑 (只有在未润色时才显示确认按钮)
if st.session_state.selected_prompts and not st.session_state.polished_text:
        st.divider()
        if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
            # 💡 核心逻辑：把当前生成的方案里“没被选中的”丢进右侧历史
            abandoned = [p for p in st.session_state.generated_cache if p not in st.session_state.selected_prompts]
            if abandoned:
                # 将丢弃的方案追加到历史档案顶部
                st.session_state.history_log = abandoned + st.session_state.history_log
            
            # 然后清空中间展示区，只保留选中的在润色
            st.session_state.generated_cache = [] 
            
            with st.spinner("AI 注入灵魂中..."):
                # ... (后续 AI 润色请求逻辑保持不变) ...
                combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                if chaos_level <= 35: v, f, n = "可爱治愈", "软萌圆润", "陪伴"
                elif chaos_level <= 75: v, f, n = "日式传统", "黑线重彩", "沉淀"
                else: v, f, n = "欧美极简", "力量解构", "破局"
                system_prompt = f"刺青策展人视角。风格：{v}，强度：{chaos_level}。融入‘纹身贴’。格式：方案X：[内容]"
                try:
                    res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"system","content":system_prompt},{"role":"user","content":combined_input}], temperature=0.8).choices[0].message.content
                    st.session_state.polished_text = res
                    st.rerun()
                except: st.error("润色失败")

    if st.session_state.polished_text:
        st.divider(); st.subheader("🎨 艺术润色成品")
        st.text_area("文案预览：", st.session_state.polished_text, height=400)
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("🚀 发送到自动化", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = st.session_state.polished_text; st.switch_page("pages/02_automation.py")
        with c_b2:
            if st.button("🔄 重新调配 (解锁所有)", use_container_width=True):
                st.session_state.polished_text = ""; st.rerun()
