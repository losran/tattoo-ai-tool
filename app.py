import streamlit as st
import requests, base64, time
from openai import OpenAI
# 📍 引入样式管理器 (保持你现在的视觉架构)
from style_manager import apply_pro_style, render_unified_sidebar

# --- 1. 核心配置 (必须第一行) ---
st.set_page_config(layout="wide", page_title="Tattoo AI Workbench")

# --- 2. 初始化 API 和 数据库配置 (下午的功能逻辑) ---
try:
    client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except:
    st.error("⚠️ 请配置 secrets.toml 中的 DEEPSEEK_KEY 和 GITHUB_TOKEN")
    st.stop()

REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

# --- 3. 核心工具函数 (复活下午的逻辑) ---
def get_data(filename):
    """GitHub 获取"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    except: pass
    return []

def sync_data(filename, data_list):
    """GitHub 同步"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        get_resp = requests.get(url, headers=headers).json()
        content_str = "\n".join(sorted(list(set(data_list))))
        b64_content = base64.b64encode(content_str.encode()).decode()
        requests.put(url, headers=headers, json={
            "message": "update from mirror tool",
            "content": b64_content,
            "sha": get_resp.get('sha')
        })
    except: st.error("同步失败")

# --- 4. 状态初始化 ---
if 'db' not in st.session_state:
    st.session_state.db = {k: get_data(v) for k, v in FILES.items()}
if 'input_val' not in st.session_state: st.session_state.input_val = ""
if 'ai_results' not in st.session_state: st.session_state.ai_results = [] # 存储AI拆解结果
if 'is_open' not in st.session_state: st.session_state.is_open = True

# --- 5. 注入视觉 (新版样式) ---
apply_pro_style()

# 侧边栏：使用真实数据驱动统计
real_counts = {k: len(v) for k, v in st.session_state.db.items()}
render_unified_sidebar(real_counts)

# --- 6. 顶层开关 (镜像布局核心) ---
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon, help="切换仓库显示"):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

# --- 7. 主布局结构 ---
if st.session_state.is_open:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# === 中间：核心工作台 (接入 AI 逻辑) ===
with col_main:
    st.title("⚡ 智能入库")
    
    # 输入框 (绑定 input_val 以便点选填入)
    user_text = st.text_area("提示词编辑区", value=st.session_state.input_val, height=300, label_visibility="collapsed")
    st.session_state.input_val = user_text

    # AI 预览结果区 (下午的功能)
    if st.session_state.ai_results:
        st.markdown("#### AI 拆解预览")
        st.caption("勾选确认入库：")
        
        # 收集选中的
        selected_to_save = []
        
        # 按分类显示预览
        for cat in FILES.keys():
            items = [x for x in st.session_state.ai_results if x['cat'] == cat]
            if items:
                st.markdown(f"**{cat}**")
                cols = st.columns(4)
                for i, item in enumerate(items):
                    with cols[i % 4]:
                        # 使用 toggle 或 checkbox 看起来更像标签
                        if st.checkbox(item['val'], value=True, key=f"new_{item['val']}_{i}"):
                            selected_to_save.append(item)
        
        st.write("")
        c_save, c_clear = st.columns([1, 4])
        if c_save.button("📥 一键入库", type="primary", use_container_width=True):
            # 执行真实入库同步
            for item in selected_to_save:
                cat = item['cat']
                if item['val'] not in st.session_state.db[cat]:
                    st.session_state.db[cat].append(item['val'])
                    sync_data(FILES[cat], st.session_state.db[cat])
            st.session_state.ai_results = []
            st.success("已同步至 GitHub！")
            time.sleep(1)
            st.rerun()
            
        if c_clear.button("清空预览"):
            st.session_state.ai_results = []
            st.rerun()

if st.button("🚀 开始 AI 拆解", type="primary", use_container_width=True):
            if user_text:
                with st.spinner("DeepSeek 正在解析五维结构..."):
                    # --- 💡 核心修改：Prompt 2.0 (针对纹身贴优化版) ---
                    prompt = f"""
                                        你是一位【资深纹身贴纸设计师】，只使用中文进行专业设计表达。
                    
                    请将用户的描述，转化为【适用于 Midjourney 的设计语义拆解】，并严格填入五维模型。
                    
                    【语言强制规则 - 必须遵守】：
                    1. 最终输出内容必须 100% 为中文。
                    2. 不允许出现任何英文单词、字母、缩写。
                    3. 所有风格、材质、情绪，必须使用设计行业常用中文表达。
                    4. 禁止音译，禁止保留英文原词。
                    
                    【核心原则】：
                    1. 材质锁定：必须体现为“纹身贴”，白底、模切、干净线条、矢量感、安全墨水质感。
                    2. 拒绝插画感：无背景、无光影渲染、只保留图案主体。
                    3. 创意升维：在用户描述基础上，注入「外星情绪」调性（冷感、怪诞、未来、极简）。
                    
                    【五维模型定义】：
                    Subject（主体）：具体视觉主体 + 材质修饰
                    Action（动态）：形态变化或交互状态
                    Style（风格）：明确的视觉设计风格
                    Mood（情绪）：整体情感气质
                    Usage（部位）：推荐贴附位置
                    
                    【原文】：{user_text}
                    
                    【输出格式】：
                    Subject:液态金属质感的机械心脏|Action:正在融化并向下滴落|Style:Y2K 酸性未来图形风格|Mood:冷感、锋利、叛逆|Usage:手臂
                    """
                    try:
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.1
                        ).choices[0].message.content
                        
                        # 解析逻辑 (保持不变)
                        parsed = []
                        clean = res.replace("**", "").replace("\n", "|").replace("：", ":")
                        for item in clean.split("|"):
                            if ":" in item:
                                cat, val = item.split(":", 1)
                                for key in FILES.keys():
                                    if key.lower() in cat.lower():
                                        for w in val.replace(",", "/").split("/"):
                                            w = w.strip()
                                            if w and w not in ["无", "N/A"]: parsed.append({"cat": key, "val": w})
                        st.session_state.ai_results = parsed
                        st.rerun()
                    except Exception as e: st.error(str(e))

# === 右侧：仓库管理 (接入真实 GitHub 数据) ===
if st.session_state.is_open:
    with col_right:
        st.markdown("### 📦 仓库管理")
        # 选择查看真实分类
        cat_view = st.selectbox("类型", list(FILES.keys()), label_visibility="collapsed")
        
        # 获取当前分类的真实数据
        current_words = st.session_state.db.get(cat_view, [])
        
        st.write("")
        # 📍 这里的 UI 是你最喜欢的：文字和叉号合并在一个视觉框内
        # 但这次我们循环的是 current_words (真实数据)
        
        if current_words:
            # 使用容器让列表可滚动，不把页面撑太长
            with st.container(height=600):
                for idx, w in enumerate(current_words):
                    # 极细 column 模拟标签
                    t_col, x_col = st.columns([5, 1.2])
                    
                    with t_col:
                        # 左边：点击 = 添加到输入框
                        if st.button(f" {w}", key=f"add_{cat_view}_{idx}", use_container_width=True):
                            st.session_state.input_val += f" {w}"
                            st.rerun()
                    
                    with x_col:
                        # 右边：点击 = 从 GitHub 删除
                        if st.button("✕", key=f"del_{cat_view}_{idx}", use_container_width=True):
                            # 真实的删除逻辑
                            new_list = [x for x in current_words if x != w]
                            st.session_state.db[cat_view] = new_list
                            sync_data(FILES[cat_view], new_list) # 同步回 GitHub
                            st.toast(f"已删除: {w}")
                            st.rerun()
        else:
            st.caption("该分类暂无数据")



