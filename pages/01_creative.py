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

# 💡 初始化核心变量
for key in ['selected_prompts', 'generated_cache', 'history_log', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if 'editor' in key or 'text' in key else []
        
# 🔒 定义全局锁定状态
is_working = len(st.session_state.polished_text) > 0

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 🟢 右侧：仓库管理 (上) + 历史记录 (下) ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    
    # 1. 仓库管理容器
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

    # 📜 历史档案区 (永驻下方)
    st.divider()
    st.subheader("📜 历史档案")
    if st.session_state.history_log:
        with st.container(height=400, border=True):
            for h_idx, h_text in enumerate(st.session_state.history_log):
                is_checked = h_text in st.session_state.selected_prompts
                if st.checkbox(f"备选 {h_idx+1}: {h_text}", key=f"h_l_{h_idx}", value=is_checked, disabled=is_working):
                    if not is_working:
                        if h_text not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(h_text)
                            st.rerun()
        
        if st.button("🗑️ 清空历史", use_container_width=True, disabled=is_working):
            st.session_state.history_log = []
            st.rerun()

# --- 🔵 左侧：核心生成区 ---
with col_main:
    # 1. 双轨控制器：审美流派 + 混乱脑洞
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        # 0可爱, 30水彩, 60日式, 100欧美
        style_spectrum = st.slider("🎨 审美光谱 (流派方向)", 0, 100, 55, help="0:可爱柔美 | 30:轻盈水彩 | 60:浓重日式 | 100:硬朗极简")
    with col_cfg2:
        chaos_level = st.slider("🌀 混乱程度 (创意脑洞)", 0, 100, 30, help="值越高，AI越倾向于超现实的、出人意料的意象碰撞")

    intent_input = st.text_area("✍️ 组合意图输入框", value=st.session_state.manual_editor, placeholder="输入核心关键词，如：宇航员、玫瑰...", disabled=is_working)
    st.session_state.manual_editor = intent_input

    # 2. 按钮行：数量选择 + 激发按钮
    col_btn_l, col_btn_r = st.columns([1, 4]) # 1:4 的比例，让按钮占主体
    with col_btn_l:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed") # 隐藏标签更整洁
    with col_btn_r:
        btn_label = "🔥 激发创意组合"
        if st.button(btn_label, type="primary", use_container_width=True, disabled=is_working):
            db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
            
            # --- A. 根据“审美光谱”确定视觉DNA ---
            if style_spectrum <= 15:
                style_dna = "风格：可爱柔美、治愈系。特点：线条圆滑、意象温馨、拒绝硬色调。"
            elif style_spectrum <= 45:
                style_dna = "风格：现代水彩插画。特点：灵动晕染、光影虚实结合、意象轻盈。"
            elif style_spectrum <= 80:
                style_dna = "风格：日式传统/Old School。特点：粗黑线条、对比色强烈、构图饱满张扬。"
            else:
                style_dna = "风格：欧美极简主义。特点：硬朗直线、几何解构、高度概括、冷峻感。"

            # --- B. 根据“混乱程度”决定AI随机性 ---
            # 脑洞越大，Temperature越高，抽词范围越广
            dynamic_temp = 0.4 + (chaos_level / 100) * 0.55 
            sample_size = int(15 + (chaos_level / 100) * 20)

            with st.spinner(f"正在以 {chaos_level}% 脑洞碰撞创意..."):
                sample_db = {k: random.sample(v, min(len(v), sample_size)) for k, v in db_all.items()}
                
                fast_prompt = f"""
                你是一位跨界纹身艺术大师。
                意图：{intent_input}
                视觉流派锁定：{style_dna}
                创意发散度：{chaos_level}/100（混乱度高则允许超现实、荒诞的组合）

                任务：基于意图并参考词库，生成 {num} 个方案。
                要求：
                1. 线条感和视觉意象必须符合上述“视觉流派”描述。
                2. 方案格式：主体，动作，风格，氛围，部位
                3. 直接返回结果，每行一个，禁止废话。
                词库参考：{sample_db}
                """
                
                try:
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": fast_prompt}],
                        temperature=dynamic_temp
                    )
                    raw_list = res.choices[0].message.content.strip().split('\n')
                    st.session_state.generated_cache = [line.strip() for line in raw_list if "，" in line][:num]
                    st.rerun()
                except Exception as e:
                    st.error(f"激发失败: {e}")
                    
    # 🎲 方案筛选 (中间桌面)
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 方案筛选")
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                if st.button(f"{idx+1}. {p}", key=f"gen_{idx}", 
                             type="primary" if is_sel else "secondary", 
                             disabled=is_working, use_container_width=True):
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
            if st.button("🗑️ 清除当前", use_container_width=True, disabled=is_working):
                st.session_state.generated_cache = []; st.session_state.selected_prompts = []
                st.rerun()

# --- 🔵 精准加固后的润色逻辑 ---
    if st.session_state.selected_prompts and not st.session_state.polished_text:
        st.divider()
        if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
            # 1. 强制归档：将生成的 cache 中未选中的方案移入 history_log
            try:
                if 'generated_cache' in st.session_state and st.session_state.generated_cache:
                    abandoned = [p for p in st.session_state.generated_cache if p not in st.session_state.selected_prompts]
                    if abandoned:
                        # 确保 history_log 是列表并追加
                        if not isinstance(st.session_state.history_log, list):
                            st.session_state.history_log = []
                        st.session_state.history_log = abandoned + st.session_state.history_log
                    
                    # 清空当前展示，完成“迁移”视觉效果
                    st.session_state.generated_cache = []
            except Exception as e:
                st.error(f"归档过程出错: {e}")

            # 2. 执行润色
            with st.spinner("AI 注入灵魂中..."):
                try:
                    # 构造纯净的输入文本
                    input_text = "\n".join([f"方案{idx+1}: {p}" for idx, p in enumerate(st.session_state.selected_prompts)])
                    
                    # 审美光谱映射
                    if chaos_level <= 35: v, f, n = "可爱治愈", "软萌圆润", "陪伴"
                    elif chaos_level <= 75: v, f, n = "日式传统", "黑线重彩", "沉淀"
                    else: v, f, n = "欧美极简", "力量解构", "破局"
                    
                    sys_p = f"你是一位资深刺青策展人。风格基调：{v}。请将方案润色为极具艺术感的纹身描述。"
                    
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": sys_p},
                            {"role": "user", "content": input_text}
                        ],
                        temperature=0.7,
                        timeout=30 # 增加超时保护
                    )
                    
                    st.session_state.polished_text = response.choices[0].message.content
                    st.rerun()
                except Exception as e:
                    st.error(f"润色失败原因: {e}")
                    # 如果失败了，建议不要清空 generated_cache，让用户可以重试

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
