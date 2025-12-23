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
        
def ai_pre_filter(category, user_intent, inventory, limit=15):
    """
    智能预选词库：仅在有输入意图时调用
    """
    if not user_intent or len(inventory) <= limit:
        return random.sample(inventory, min(len(inventory), limit))
    
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：从中挑选出最符合意图的 {limit} 个词。只返回词汇，逗号分隔。"
    try:
        res = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "user", "content": prompt}], 
            temperature=0.3
        )
        filtered_words = res.choices[0].message.content.replace("，", ",").split(",")
        # 确保选出来的词确实在词库里
        valid_words = [w.strip() for w in filtered_words if w.strip() in inventory]
        return valid_words if valid_words else random.sample(inventory, limit)
    except:
        return random.sample(inventory, limit)
        
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
    # 1. 顶部控制栏：风格调性 + 创意混乱度
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        style_tone = st.select_slider(
            "🎨 风格调性选择",
            options=["自由盲盒", "可爱柔美", "轻盈水彩", "日式传统", "欧美极简"],
            value="日式传统"
        )
    with col_cfg2:
        chaos_level = st.slider("🌀 创意碰撞 (混乱度)", 0, 100, 50)

    # 2. 意图输入
    intent_input = st.text_area("✍️ 组合意图输入框", placeholder="输入关键词，如：宇航员、玫瑰...", height=100)
    st.session_state.manual_editor = intent_input

    # 3. 按钮行：左侧激发按钮 + 右侧数量数字
    col_btn_btn, col_btn_num = st.columns([4, 1]) 
    with col_btn_btn:
        execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True, disabled=is_working)
    with col_btn_num:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed")

    # --- 按钮执行逻辑 ---
    if execute_button:
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        with st.spinner("AI 正在深度调配中..."):
            has_intent = bool(intent_input.strip())
            
            # A. 风格指令判定
            if style_tone == "自由盲盒":
                style_instruction = "不限风格，极致随机跨界。"
            else:
                style_instruction = f"将意图与【{style_tone}】风格强制融合，即使冲突也要做风格化变形。"

            # B. 智能词库采样
            smart_sample_db = {}
            for k, v in db_all.items():
                if has_intent:
                    try:
                        smart_sample_db[k] = ai_pre_filter(k, intent_input, v, limit=15)
                    except:
                        smart_sample_db[k] = random.sample(v, min(len(v), 15))
                else:
                    s_size = int(15 + (chaos_level / 100) * 20)
                    smart_sample_db[k] = random.sample(v, min(len(v), s_size))

            # C. 核心指令包 (强力纠正格式，严禁 JSON)
            fast_prompt = f"""
            任务：作为纹身策展大师，生成 {num} 个方案。
            意图：{intent_input if has_intent else '完全随机灵感'}
            调性：{style_instruction}
            混乱度：{chaos_level}/100

            【硬性要求】：
            1. 严禁返回任何大括号{{}}、严禁返回JSON格式、严禁返回“主体：”等键值对！
            2. 必须严格遵守下方示例格式，每行只有5个元素，用中文逗号“，”隔开。
            3. 只输出列表，不准有任何解释。

            【格式示例】：
            机械心脏，跳动，赛博朋克，压抑，胸口
            
            【参考词库】：
            {smart_sample_db}

            【立即开始生成列表】：
            """

            # D. 发送请求
            try:
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": fast_prompt}],
                    temperature= 0.4 + (chaos_level / 100) * 0.5
                )
                raw_content = res.choices[0].message.content.strip()
                
                # E. 强力清洗数据，确保卡片显示正常
                raw_list = raw_content.split('\n')
                st.session_state.generated_cache = [
                    line.replace('"', '').replace('{', '').replace('}', '').strip() 
                    for line in raw_list 
                    if "，" in line and "{" not in line
                ][:num]
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

# --- 🔵 润色逻辑：基于风格调性与意图融合 ---
if st.session_state.selected_prompts and not st.session_state.polished_text:
    st.divider()
    if st.button("✨ 确认方案并开始润色", type="primary", use_container_width=True):
        
        # 1. 自动归档：把没选中的方案丢进历史
        if st.session_state.generated_cache:
            abandoned = [p for p in st.session_state.generated_cache if p not in st.session_state.selected_prompts]
            if abandoned:
                st.session_state.history_log = abandoned + st.session_state.history_log
            st.session_state.generated_cache = []

        # 2. 执行润色
        with st.spinner("AI 正在注入艺术灵魂..."):
            try:
                # 构造输入
                input_text = "\n".join([f"方案{idx+1}: {p}" for idx, p in enumerate(st.session_state.selected_prompts)])
                
                # --- 核心：风格调性映射 (替换掉原来的 chaos_level 判断) ---
                # style_tone 是我们刚才设定的 st.radio 的值
                if style_tone == "可爱柔美":
                    v, f, n = "可爱治愈", "线条圆润、色彩清新、充满软萌感", "陪伴与温暖"
                elif style_tone == "轻盈水彩":
                    v, f, n = "插画水彩", "光影斑驳、虚实结合、边缘柔和", "灵动与自由"
                elif style_tone == "日式传统":
                    v, f, n = "日式 Old School", "重彩黑线、张力十足、极具东方韵味", "力量与宿命"
                elif style_tone == "欧美极简":
                    v, f, n = "欧美极简线条", "几何解构、冷峻利落、拒绝冗余", "破局与纯粹"
                else: # 自由盲盒
                    v, f, n = "前卫艺术", "跨界碰撞、不拘一格、充满意外惊喜", "自我表达"

                # 构造系统提示词：要求 AI 融合用户的意图
                sys_p = f"""你是一位刺青策展大师。
                当前艺术调性：{v}。
                视觉特征要求：{f}。
                情感基调：{n}。
                
                【核心任务】：
                请将用户选中的方案润色为极具艺术感的纹身描述。
                如果原始方案与调性存在反差（如：日式主题遇到可爱调性），
                请发挥想象力，创作出一种“反差萌”或“跨界风格”的文学描述。
                每条描述字数适中，包含视觉细节。"""
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": sys_p},
                        {"role": "user", "content": f"用户初始意图：{intent_input}\n\n待润色方案：\n{input_text}"}
                    ],
                    temperature=0.7,
                    timeout=30
                )
                
                st.session_state.polished_text = response.choices[0].message.content
                st.rerun()
                
            except Exception as e:
                st.error(f"润色失败: {e}")

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
