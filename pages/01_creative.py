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
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：从中挑选出符合意图的 {limit} 个词。只返回词汇，逗号分隔。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        filtered_words = res.choices[0].message.content.replace("，", ",").split(",")
        valid_words = [w.strip() for w in filtered_words if w.strip() in inventory]
        return valid_words if valid_words else random.sample(inventory, limit)
    except: return random.sample(inventory, limit)

# --- 3. UI 布局与 Session 初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

# 初始化 Session
for key in ['selected_prompts', 'generated_cache', 'history_log', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if 'editor' in key or 'text' in key else []

# 全局锁定状态判断
is_working = len(st.session_state.polished_text) > 0

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 🟢 右侧：仓库管理 + 历史档案 ---
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
                        if w not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(w)
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps:
                    if st.checkbox(i, key=f"insp_lib_{abs(hash(i))}", disabled=is_working):
                        if i not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(i)

    st.divider()
    st.subheader("📜 历史档案")
    if st.session_state.history_log:
        with st.container(height=400, border=True):
            for h_idx, h_text in enumerate(st.session_state.history_log):
                is_checked = h_text in st.session_state.selected_prompts
                if st.checkbox(f"备选 {h_idx+1}: {h_text}", key=f"h_l_{h_idx}", value=is_checked, disabled=is_working):
                    if h_text not in st.session_state.selected_prompts:
                        st.session_state.selected_prompts.append(h_text)
                        st.rerun()

# --- 🔵 左侧：核心生成区 ---
with col_main:
    # 1. 控制台
    c1, c2 = st.columns(2)
    with c1:
        # 统一变量名：style_tone
        style_tone = st.radio("🎭 风格调性点选", options=["自由盲盒", "可爱柔美", "轻盈水彩", "日式传统", "欧美极简"], horizontal=True, index=3)
    with c2:
        # 统一变量名：chaos_level
        chaos_level = st.slider("🌀 创意碰撞 (混乱度)", 0, 100, 50)

    # 2. 意图
    intent_input = st.text_area("✍️ 组合意图输入框", placeholder="输入关键词...", height=100)
    st.session_state.manual_editor = intent_input

    # 3. 执行行
    cb_btn, cb_num = st.columns([4, 1])
    with cb_btn:
        execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True)
    with cb_num:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed")

    # --- 核心激发逻辑 ---
    if execute_button:
        # 点击即强制解锁
        st.session_state.polished_text = ""
        st.session_state.generated_cache = []
        
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        with st.spinner("🚀 AI 正在释放灵感碰撞..."):
            has_intent = bool(intent_input.strip())
            
            style_map = {
                "可爱柔美": "治愈系可爱纹身风格",
                "轻盈水彩": "透明插画水彩风格",
                "日式传统": "日式 Old School 风格",
                "欧美极简": "欧美冷峻极简风格",
                "自由盲盒": "前卫跨界艺术风格"
            }
            tone_name = style_map.get(style_tone, "自由发挥")

            smart_db = {}
            for k, v in db_all.items():
                if not v: v = ["灵感节点"]
                if has_intent:
                    smart_db[k] = ai_pre_filter(k, intent_input, v, limit=20)
                else:
                    smart_db[k] = random.sample(v, min(len(v), 20))

            # 找回那种“自由堆叠词”的 Prompt
            fast_prompt = f"""
            你是一位资深纹身设计师。围绕【{intent_input if has_intent else '自由灵感'}】设计 {num} 个方案。
            必须体现：{tone_name}。
            
            要求：
            1. 自由从库中拼贴 5-8 个词汇，形成“风格词，主体词，动作词，意象词，氛围词，部位”的艺术长串。
            2. 每个方案占一行，必须用中文逗号“，”隔开。
            3. 严禁 JSON，严禁大括号，严禁输出“方案1:”字样。
            
            参考库：{smart_db}
            """

            try:
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": fast_prompt}],
                    temperature=0.4 + (chaos_level / 100) * 0.5
                )
                raw = res.choices[0].message.content.strip()
                # 强效清洗
                lines = raw.split('\n')
                st.session_state.generated_cache = [
                    l.replace('{','').replace('}','').replace('"','').replace('方案','').split(':')[-1].strip()
                    for l in lines if "，" in l or "," in l
                ][:num]
                st.rerun()
            except Exception as e:
                st.error(f"激发失败: {e}")

    # --- 4. 方案筛选区 ---
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 方案筛选")
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                if st.button(f"{idx+1}. {p}", key=f"g_{idx}", type="primary" if is_sel else "secondary", use_container_width=True):
                    if is_sel: st.session_state.selected_prompts.remove(p)
                    else: st.session_state.selected_prompts.append(p)
                    st.rerun()
        
        # 底部管理按钮：视觉区分
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
                st.session_state.generated_cache = []; st.session_state.selected_prompts = []
                st.session_state.polished_text = ""; st.rerun()

# --- 5. 润色区域逻辑（保持稳健） ---
if st.session_state.selected_prompts and not st.session_state.polished_text:
    st.divider()
    if st.button("✨ 确认并开始艺术润色", type="primary", use_container_width=True):
        st.session_state.generated_cache = [] # 自动清理桌面
        with st.spinner("AI 正在深度润色中..."):
            try:
                input_p = "\n".join(st.session_state.selected_prompts)
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一位纹身策展人。风格调性锁定：{style_tone}"},
                        {"role": "user", "content": f"润色这些词条为具有文学感的刺青方案：\n{input_p}"}
                    ],
                    temperature=0.7
                )
                st.session_state.polished_text = res.choices[0].message.content
                st.rerun()
            except Exception as e:
                st.error(f"润色失败: {e}")

if st.session_state.polished_text:
    st.divider(); st.subheader("🎨 润色成品")
    st.text_area("文案内容：", st.session_state.polished_text, height=300)
    if st.button("🔄 重新调配 (解锁)", use_container_width=True):
        st.session_state.polished_text = ""; st.rerun()
