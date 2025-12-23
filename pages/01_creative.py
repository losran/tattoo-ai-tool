import streamlit as st
import json
import os
import random
import numpy as np
import requests
import base64
from openai import OpenAI
from style_manager import apply_pro_style

# 📍 傻瓜调用：全站视觉一键同步
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

# --- 2. 核心 AI 选词引擎 ---
def smart_sample_with_ai(category, user_intent, inventory):
    if not user_intent or not user_intent.strip():
        return random.choice(inventory) if inventory else "空"
    
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：选一个最符合意图的词。只返回词汇本身。"
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        picked_word = res.choices[0].message.content.strip()
        return picked_word if picked_word in inventory else random.choice(inventory)
    except:
        return random.choice(inventory)

# --- 3. 工具函数 ---
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

# --- 4. UI 布局与初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

for key in ['selected_prompts', 'generated_cache', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if ('editor' in key or 'text' in key) else []

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 右侧：仓库管理 ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    if mode == "素材仓库":
        cat = st.selectbox("当前分类", list(WAREHOUSE.keys()))
        words = get_github_data(WAREHOUSE[cat])
        if words:
            selected_items = []
            with st.container(height=500, border=True):
                for w in words:
                    if st.checkbox(f" {w}", key=f"manage_{cat}_{w}"): selected_items.append(w)
            if selected_items:
                if st.button("➕ 导入到组合输入框", use_container_width=True):
                    st.session_state.manual_editor = f"{st.session_state.manual_editor} {' '.join(selected_items)}".strip()
                    st.rerun()
                if st.button(f"🗑️ 删除选中项", type="primary", use_container_width=True):
                    remaining = [w for w in words if w not in selected_items]
                    save_to_github(WAREHOUSE[cat], remaining); st.rerun()
    else:
        insps = get_github_data(GALLERY_FILE)
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
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1: num = st.slider("生成方案数量", 1, 10, 6)
    # 💡 审美光谱滑块修改
    with col_cfg2: chaos_level = st.slider("🎨 审美光谱：🌸 可爱 — 🐉 日式 — 📐 欧美极简", 0, 100, 55)
    
    intent_input = st.text_area("✍️ 组合意图输入框", value=st.session_state.manual_editor)
    st.session_state.manual_editor = intent_input

    if st.button("🔥 激发创意组合", type="primary", use_container_width=True):
        st.session_state.polished_text = "" 
        st.session_state.generated_cache = []
        st.session_state.selected_prompts = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        if not any(db_all.values()):
            st.error("⚠️ 仓库是空的！")
        else:
            with st.spinner("AI 正在挑选..."):
                for _ in range(num):
                    s = smart_sample_with_ai("Subject", intent_input, db_all["Subject"])
                    a = smart_sample_with_ai("Action", intent_input, db_all["Action"])
                    st_val = smart_sample_with_ai("Style", intent_input, db_all["Style"])
                    m = smart_sample_with_ai("Mood", intent_input, db_all["Mood"])
                    u = smart_sample_with_ai("Usage", intent_input, db_all["Usage"])
                    combined_p = f"{s}，{a}，{st_val}风格，{m}氛围，纹在{u}"
                    st.session_state.generated_cache.append(combined_p)
            st.rerun()

# 3. 🎲 方案展示与筛选
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 方案筛选 (点击卡片进行调配)")
        
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                if st.button(f"方案 {idx+1}\n\n{p}", key=f"sel_{idx}", type="primary" if is_sel else "secondary"):
                    if is_sel: st.session_state.selected_prompts.remove(p)
                    else: st.session_state.selected_prompts.append(p)
                    st.rerun()
        
        # --- 🚀 新增：方案筛选下方的功能按钮 ---
        st.write("") # 留点间隙
        c_tool1, c_tool2 = st.columns(2)
        with c_tool1:
            if st.button("💾 存入成品库 (保存当前选中组合)", use_container_width=True):
                if st.session_state.selected_prompts:
                    current = get_github_data(GALLERY_FILE)
                    current.extend(st.session_state.selected_prompts)
                    if save_to_github(GALLERY_FILE, current):
                        st.success(f"已将 {len(st.session_state.selected_prompts)} 组方案存入成品库")
                else:
                    st.warning("请先勾选上方方案再进行存储")
                    
        with c_tool2:
            if st.button("🗑️ 清除所有已选/已生成", use_container_width=True):
                st.session_state.generated_cache = []
                st.session_state.selected_prompts = []
                st.session_state.polished_text = ""
                st.rerun()

    # ✨ 核心缩进正确版润色逻辑
    if st.session_state.selected_prompts and not st.session_state.polished_text:
        st.divider()
        if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
            with st.spinner("AI 正在根据审美光谱注入灵魂..."):
                combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                
                # --- 🎨 审美光谱动态逻辑 ---
                if chaos_level <= 35:
                    style_vibe = "【可爱治愈系】。风格偏向东亚萌系、马卡龙配色、软糯线条。"
                    visual_focus = "侧重于描述图案的软萌感、圆润轮廓。"
                    narrative_type = "陪伴"
                elif chaos_level <= 75:
                    style_vibe = "【日式传统/Old School】。强调工整重彩、经典浮世绘复古构图。"
                    visual_focus = "侧重于描述黑线张力、色彩浓郁。"
                    narrative_type = "沉淀"
                else:
                    style_vibe = "【欧美极简/硬核先锋】。风格偏向加粗单黑线条、几何解构。"
                    visual_focus = "侧重于描述线条的绝对力量、留白艺术。"
                    narrative_type = "破局"

                system_prompt = f"你是一位纹身艺术策展人。当前审美坐标：{style_vibe}。表现重点：{visual_focus}。风格强度：{chaos_level}/100。请以‘{narrative_type}’为基调扩写。必须融入‘纹身贴’。格式：方案X：[扩写内容]"
                
                try:
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined_input}],
                        temperature=0.7 + (chaos_level / 200)
                    ).choices[0].message.content
                    st.session_state.polished_text = res
                    st.rerun()
                except Exception as e:
                    st.error(f"润色失败: {e}")

# 5. 展示润色成品 (删除存入库功能，只保留自动化和重调)
    if st.session_state.polished_text:
        st.divider()
        st.subheader("🎨 艺术润色成品")
        final_content = st.text_area("文案预览：", st.session_state.polished_text, height=400)
        
        # 只保留两个核心按钮
        c_btn_auto, c_btn_reset = st.columns(2)
        with c_btn_auto:
            if st.button("🚀 发送到自动化", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
        with c_btn_reset:
            if st.button("🔄 重新调配", use_container_width=True):
                st.session_state.polished_text = ""
                # 这里不清除 selected_prompts，方便用户微调
                st.rerun()
