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
    # 1. 顶部控制：点选流派 + 创意混乱度
    # 使用 try-except 保护，防止滑块初始化报错
    try:
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            style_tone = st.radio(
                "🎭 风格调性点选",
                options=["自由盲盒", "可爱柔美", "轻盈水彩", "日式传统", "欧美极简"],
                horizontal=True,
                index=3,
                key="style_tone_selector" # 绑定固定Key
            )
        with col_cfg2:
            chaos_level = st.slider("🌀 创意碰撞 (混乱度)", 0, 100, 50, key="chaos_slider")
    except Exception as e:
        st.error(f"UI组件初始化失败，请刷新页面: {e}")

    # 2. 意图输入
    intent_input = st.text_area("✍️ 组合意图输入框", placeholder="输入关键词，如：宇航员、玫瑰...", height=100)
    st.session_state.manual_editor = intent_input

    # 3. 按钮行：左侧激发按钮 + 右侧数量选择
    col_btn_btn, col_btn_num = st.columns([4.2, 1]) 
    with col_btn_btn:
        # 这里移除 disabled=is_working，确保无论何时你都能点它！
        execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True)
    with col_btn_num:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed")

    # --- 核心执行逻辑：确保逻辑闭环 ---
    if execute_button:
        # ⚡ 核心保护：点击即解锁，防止逻辑死锁
        st.session_state.polished_text = "" 
        st.session_state.generated_cache = []
        
        with st.spinner("🚀 灵感正在超维碰撞中..."):
            try:
                # A. 读取词库并加入防空保护
                db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
                if not any(db_all.values()):
                    st.warning("⚠️ 词库读取为空，请检查网络连接或 GitHub 仓库。")
                    st.stop()

                has_intent = bool(intent_input.strip())
                
                # B. 风格定性
                style_mapping = {
                    "可爱柔美": "治愈可爱线条风格",
                    "轻盈水彩": "透明叠色水彩风格",
                    "日式传统": "日式 Old School 风格",
                    "欧美极简": "欧美极简几何风格",
                    "自由盲盒": "前卫跨界艺术风格"
                }
                tone_name = style_mapping.get(style_tone, "自由发挥")

                # C. 智能抽样 (增加 Try 保护)
                smart_sample_db = {}
                for k, v in db_all.items():
                    if not v: v = ["灵感节点"] # 兜底词汇
                    if has_intent:
                        try:
                            smart_sample_db[k] = ai_pre_filter(k, intent_input, v, limit=20)
                        except:
                            smart_sample_db[k] = random.sample(v, min(len(v), 20))
                    else:
                        smart_sample_db[k] = random.sample(v, min(len(v), 20))

                # D. 构造 Prompt：恢复放飞模式，明确禁止 JSON
                fast_prompt = f"""
                作为纹身设计师，围绕意图【{intent_input if has_intent else '自由发挥'}】进行创作。
                必须锁定调性：{tone_name}。
                
                要求：
                1. 自由堆叠 5-8 个词汇，形成“风格+主体+氛围+部位”的艺术拼贴。
                2. 每行一个方案，用中文逗号隔开。
                3. 严禁 JSON，严禁大括号，严禁输出“方案1:”这种废话。
                
                参考词库：{smart_sample_db}
                """

                # E. API 调用加温控
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": fast_prompt}],
                    temperature=0.5 + (chaos_level / 100) * 0.45,
                    timeout=20 # 设置超时防止挂死
                )
                
                # F. 结果清洗与展示
                raw_content = res.choices[0].message.content.strip()
                raw_list = raw_content.split('\n')
                # 过滤掉所有不含逗号的垃圾信息
                clean_list = [
                    line.replace('{', '').replace('}', '').replace('"', '').replace('方案', '').strip() 
                    for line in raw_list if "，" in line or "," in line
                ]
                
                if clean_list:
                    st.session_state.generated_cache = clean_list[:num]
                    st.rerun()
                else:
                    st.error("❌ AI 生成格式异常，请重试。")

            except Exception as e:
                st.error(f"💡 激发过程出错: {e}")

# --- 🎯 方案筛选区：增加一键解锁 ---
    if st.session_state.generated_cache:
        st.divider()
        st.subheader("🎲 方案筛选")
        # 渲染逻辑保持不变...
        
        # ... (中间渲染代码) ...

        # 底部工具栏
        c_tool1, c_tool2 = st.columns(2)
        with c_tool1:
            st.button("💾 确认存档", use_container_width=True, type="secondary") # 存档逻辑简化
        with c_tool2:
            if st.button("🗑️ 清空看板并强行解锁", use_container_width=True, type="secondary"):
                st.session_state.generated_cache = []
                st.session_state.selected_prompts = []
                st.session_state.polished_text = "" # 强行解锁
                st.rerun()
        
# --- 底部功能按钮区：重塑视觉区分 ---
        c_tool1, c_tool2 = st.columns(2)
        with c_tool1:
            # 使用 type="secondary" (次要按钮) 或者加一个明显的图标，并减小宽度感
            if st.button("💾 确认存档并存入成品库", use_container_width=True, type="secondary", disabled=is_working):
                if st.session_state.selected_prompts:
                    current = get_github_data(GALLERY_FILE)
                    current.extend(st.session_state.selected_prompts)
                    if save_to_github(GALLERY_FILE, current):
                        st.toast("✅ 已成功同步至 GitHub 成品库")
                    else:
                        st.error("同步失败，请检查 Token 权限")

        with c_tool2:
            # 清除按钮通常建议使用更轻量的视觉，或者加上警告色图标
            if st.button("🗑️ 一键清空当前看板", use_container_width=True, type="secondary", disabled=is_working):
                st.session_state.generated_cache = []
                st.session_state.selected_prompts = []
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
