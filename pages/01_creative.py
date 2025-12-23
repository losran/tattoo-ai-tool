import streamlit as st
import json
import os
import random
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

def ai_pre_filter(category, user_intent, inventory, limit=15):
    if not user_intent or len(inventory) <= limit:
        return random.sample(inventory, min(len(inventory), limit))
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：从挑选符合意图的 {limit} 个词。只返回词汇，逗号分隔。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        filtered = res.choices[0].message.content.replace("，", ",").split(",")
        valid = [w.strip() for w in filtered if w.strip() in inventory]
        return valid if valid else random.sample(inventory, limit)
    except: return random.sample(inventory, limit)

# --- 3. UI 布局与 Session 初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

for key in ['selected_prompts', 'generated_cache', 'history_log', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if 'editor' in key or 'text' in key else []

is_working = len(st.session_state.polished_text) > 0

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 🟢 右侧：管理区 ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    with st.container(height=300, border=True):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            if words:
                for w in words:
                    if st.checkbox(f" {w}", key=f"cat_{cat}_{w}", disabled=is_working):
                        if w not in st.session_state.selected_prompts: st.session_state.selected_prompts.append(w)
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps:
                    if st.checkbox(i, key=f"insp_{abs(hash(i))}", disabled=is_working):
                        if i not in st.session_state.selected_prompts: st.session_state.selected_prompts.append(i)
    st.divider()
    st.subheader("📜 历史档案")
    if st.session_state.history_log:
        with st.container(height=400, border=True):
            for h_idx, h_text in enumerate(st.session_state.history_log):
                if st.checkbox(f"备选 {h_idx+1}: {h_text}", key=f"h_{h_idx}", value=h_text in st.session_state.selected_prompts, disabled=is_working):
                    if h_text not in st.session_state.selected_prompts: st.session_state.selected_prompts.append(h_text); st.rerun()

# --- 🔵 左侧：生成核心区 ---
with col_main:
    c1, c2 = st.columns(2)
    with c1:
        style_tone = st.radio("🎭 风格调性点选", options=["自由盲盒", "可爱柔美", "轻盈水彩", "日式传统", "欧美极简"], horizontal=True, index=3)
    with c2:
        chaos_level = st.slider("🌀 创意碰撞 (混乱度)", 0, 100, 50)

    intent_input = st.text_area("✍️ 组合意图输入框", placeholder="输入关键词...", height=100)
    st.session_state.manual_editor = intent_input

    cb_btn, cb_num = st.columns([4, 1])
    with cb_btn:
        execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True)
    with cb_num:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed")

    if execute_button:
        st.session_state.polished_text = "" # 点击即解锁
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        with st.spinner("🚀 灵感爆发中..."):
            has_intent = bool(intent_input.strip())
            style_map = {"可爱柔美": "可爱治愈", "轻盈水彩": "透明水彩", "日式传统": "日式Old School", "欧美极简": "极简几何", "自由盲盒": "前卫跨界"}
            tone = style_map.get(style_tone, "随机")
            smart_db = {k: ai_pre_filter(k, intent_input, v, 20) if has_intent else random.sample(v, min(len(v), 20)) for k, v in db_all.items()}
            
            prompt = f"风格：{tone}。意图：{intent_input if has_intent else '自由'}。从库中拼贴5-8个词形成艺术长句，每行一个，中文逗号分隔。禁止JSON。【核心要求】：
                1. 不要死板！请从词库中自由组合 7-8 个词汇。
                2. 结构：风格 + 主体 + 随机动作 + 随机氛围 + 身体部位。
                3. 要有一种“破碎、拼贴”的艺术感，词汇之间要有反差。
                4. 输出格式：纯中文，用逗号分隔。参考库：{smart_db}"
            
            try:
                res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.5+(chaos_level/200))
                lines = res.choices[0].message.content.strip().split('\n')
                st.session_state.generated_cache = [l.split(':')[-1].strip() for l in lines if "，" in l or "," in l][:num]
                st.rerun()
            except Exception as e: st.error(f"失败: {e}")

    if st.session_state.generated_cache:
        st.divider(); st.subheader("🎲 方案筛选")
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                if st.button(f"{idx+1}. {p}", key=f"g_{idx}", type="primary" if is_sel else "secondary", use_container_width=True):
                    if is_sel: st.session_state.selected_prompts.remove(p)
                    else: st.session_state.selected_prompts.append(p)
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        ct1, ct2 = st.columns(2)
        with ct1:
            if st.button("💾 确认存入成品库", use_container_width=True, type="secondary"):
                if st.session_state.selected_prompts:
                    cur = get_github_data(GALLERY_FILE)
                    cur.extend(st.session_state.selected_prompts)
                    if save_to_github(GALLERY_FILE, cur): st.toast("✅ 已存档")
        with ct2:
            if st.button("🗑️ 清空看板并强行解锁", use_container_width=True, type="secondary"):
                st.session_state.generated_cache = []; st.session_state.selected_prompts = []; st.session_state.polished_text = ""; st.rerun()

# --- 4. 润色区与【关键自动化入口】 ---
if st.session_state.selected_prompts and not st.session_state.polished_text:
    st.divider()
    if st.button("✨ 确认并转化为绘画提示词 (含方案锚点)", type="primary", use_container_width=True):
        st.session_state.generated_cache = [] # 清理桌面
        
        with st.spinner(f"AI 正在执行【{style_tone}】风格的【{chaos_level}% 基因突变】并生成分段锚点..."):
            try:
                # 1. 风格基调 (Style DNA) - 保持你原版逻辑
                style_dict = {
                    "可爱柔美": "Vector Art, thick rounded outlines, pastel flat colors, sticker art, kawaii core, no shading",
                    "轻盈水彩": "Hand-drawn Watercolor, ink bleed effect, white negative space, artistic splash, soft edges, illustration",
                    "日式传统": "Ukiyo-e Style, bold black calligraphy lines, flat traditional colors, woodblock print texture, 2D",
                    "欧美极简": "Linework Tattoo, geometric abstraction, single weight line, black and white, minimalist vector",
                    "自由盲盒": "Pop Art, mixed media collage, glitch art, abstract shapes, bold graphic design"
                }
                current_style_tags = style_dict.get(style_tone, "2D Vector Art, clean lines")

                # 2. 混乱度逻辑 - 保持你原版逻辑
                if chaos_level <= 30:
                    chaos_instruction = "严格遵守风格定义，不要添加任何奇怪元素，保持画风纯正、传统、稳健。"
                elif chaos_level <= 70:
                    chaos_instruction = "在保持风格基础的同时，加入异质元素。例如：在传统风格中加入现代几何形状，或使用非传统的配色方案。"
                else:
                    chaos_instruction = """
                    执行【风格强行融合】：
                    1. 必须打破常规！例如：如果是日式风格，尝试用“欧美复古”或“中式可爱”材质去表现。
                    2. 制造反差感 (Contrast)！例如：可爱的外表下隐藏着水彩，或者极简线条中爆发出绚丽风光色彩。
                    3. 关键词要包含：ART, Hybrid (混合体), old school, Y2K。
                    """

                # 3. 构造 System Prompt - 微调要求让AI知道要逐行处理
                system_prompt = f"""
                你是一个专门设计【纹身贴纸 (Tattoo Sticker)】的 AI 指令专家。
                
                【绝对禁令】：
                ❌ 严禁出现：Photorealistic, 3D Render, Unreal Engine, Hyper-realistic, Photo.
                ❌ 严禁出现背景：必须是 Isolated on white background.
                
                【当前风格锚点】：
                {current_style_tags}
                
                【混乱度/融合指令 ({chaos_level}/100)】：
                {chaos_instruction}
                
                【任务】：
                将用户的**每一个**关键词方案，分别转化为中文 Prompt。
                Prompt 结构必须是：
                (Best Quality), (Tattoo Sticker:1.3), [风格词], [融合后的视觉描述], white background
                
                【输出格式】：
                请严格【逐行输出】，每一行对应一个方案。纯中文 Tag 列表，用逗号分隔。
                """

                # 4. 发送请求 (这里的 raw_input 加了编号，帮AI对齐)
                input_lines = [f"Scheme {i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)]
                raw_input = "\n".join(input_lines)
                
                res = client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请逐行处理以下方案：\n{raw_input}"}
                    ], 
                    temperature=0.6 + (chaos_level / 200)
                )
                
                # 5. 物理分段 + 锚点植入 (核心修改)
                ai_output = res.choices[0].message.content.strip()
                ai_lines = [line for line in ai_output.split('\n') if line.strip()]
                
                final_output_list = []
                # 你的物理前缀
                prefix = "(Masterpiece), (Tattoo Sticker:1.4), (2D:1.3), white background, "
                
                # 循环拼接，确保每一行都有“方案X:”
                for idx, prompt_text in enumerate(ai_lines):
                    # 防止AI回传的行数多于或少于输入，做一个安全截断
                    if idx >= len(st.session_state.selected_prompts): break
                    
                    # 清洗一下AI可能自带的序号
                    clean_prompt = prompt_text.split(':')[-1].split('.')[-1].strip()
                    clean_prompt = clean_prompt.replace("Prompt:", "").replace("提示词:", "")
                    
                    # 组装：方案X: + 前缀 + 风格 + 内容
                    formatted_line = f"方案{idx+1}: {prefix} {current_style_tags}, {clean_prompt}"
                    final_output_list.append(formatted_line)
                
                # 如果AI偶尔抽风只回了一行，这里做一个兜底，强行把所有方案都列出来
                if not final_output_list and ai_output:
                     final_output_list.append(f"方案1: {prefix} {current_style_tags}, {ai_output}")

                st.session_state.polished_text = "\n\n".join(final_output_list)
                st.rerun()

            except Exception as e: 
                st.error(f"转化失败: {e}")

if st.session_state.polished_text:
    st.divider(); st.subheader("🎨 绘图提示词 (Ready)")
    
    st.text_area("提示词预览 (已加锚点)：", st.session_state.polished_text, height=300)
    
    # 自动化入口 (保证不丢！)
    c_auto_1, c_auto_2 = st.columns(2)
    with c_auto_1:
        if st.button("🚀 发送到自动化生成", type="primary", use_container_width=True):
            st.session_state.auto_input_cache = st.session_state.polished_text
            st.switch_page("pages/02_automation.py")
    with c_auto_2:
        if st.button("🔄 重新生成 (解锁)", use_container_width=True):
            st.session_state.polished_text = ""; st.rerun()
