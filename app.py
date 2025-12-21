import streamlit as st
from openai import OpenAI
import random

# 配置 DeepSeek API
client = OpenAI(api_key='sk-b18b6a62e0374b3ebab3d961c4806a4c', base_url="https://api.deepseek.com")

# 页面配置：适配宽屏与移动端
st.set_page_config(page_title="Tattoo Studio", layout="wide", initial_sidebar_state="collapsed")

# --- 视觉样式 CSS ---
st.markdown("""
    <style>
    .asset-tag {
        display: inline-block;
        background: rgba(0, 113, 227, 0.1) !important;
        color: #0071e3 !important;
        border: 1px solid rgba(0, 113, 227, 0.2) !important;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 13px;
        margin: 3px;
        font-weight: 500;
    }
    .res-card {
        background: rgba(128, 128, 128, 0.05);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-bottom: 15px;
    }
    /* 移动端间距优化 */
    @media (max-width: 640px) {
        .stColumns { gap: 0 !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 核心状态初始化 ---
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# --- 定义拆解逻辑 ---
def handle_disassembly():
    input_val = st.session_state.temp_input 
    if input_val:
        try:
            with st.spinner('AI 正在分类零件...'):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "按 格式: 主体:X|风格:X|部位:X|氛围:X 拆解。"},
                              {"role": "user", "content": input_val}],
                    timeout=15
                )
                res_text = response.choices[0].message.content
                for item in res_text.split("|"):
                    if ":" in item:
                        k, v = item.split(":", 1)
                        if "主体" in k: st.session_state.db["主体"].append(v.strip())
                        elif "风格" in k: st.session_state.db["风格"].append(v.strip())
                        elif "部位" in k: st.session_state.db["部位"].append(v.strip())
                        elif "氛围" in k: st.session_state.db["氛围"].append(v.strip())
                
                # 成功后清空输入框
                st.session_state.input_text = "" 
                st.success("分类成功，样板已清理！")
        except Exception as e:
            st.error(f"解析失败: {e}")

# --- 侧边栏：素材录入 ---
with st.sidebar:
    st.header("📥 素材录入")
    st.text_area("样板描述", 
                 value=st.session_state.input_text, 
                 key="temp_input", 
                 placeholder="粘贴描述后点击下方按钮...", 
                 height=150)
    st.button("开始拆解并入库", use_container_width=True, type="primary", on_click=handle_disassembly)
    
    if st.button("🧹 清空所有零件库", use_container_width=True):
        st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}
        st.rerun()

# --- 主界面：资产看板 ---
st.title("🎨 纹身设计资产看板")

cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]
for i, name in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {name}")
        items = list(set(st.session_state.db[name])) # 自动去重
        if items:
            html_tags = "".join([f'<span class="asset-tag">{x}</span>' for x in items])
            st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{html_tags}</div>', unsafe_allow_html=True)
        else:
            st.caption("暂无数据")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 批量生成区：把丢失的功能找回来 ---
st.header("🎲 灵感批量生成")
# 使用更加“讲究”的滑块设计
count = st.select_slider("选择一次生成的数量", options=[1, 3, 5, 8, 12], value=3)

if st.button("✨ 立即生成创意组合", use_container_width=True, type="secondary"):
    db = st.session_state.db
    # 检查是否每个库都有零件
    if all(len(v) > 0 for v in db.values()):
        st.balloons()
        # 适配手机端：如果是宽屏则分两列，否则单列
        res_cols = st.columns(2)
        for i in range(count):
            s = random.choice(db["主体"])
            sty = random.choice(db["风格"])
            p = random.choice(db["部位"])
            v = random.choice(db["氛围"])
            
            with res_cols[i % 2]:
                st.markdown(f"""
                <div class="res-card">
                    <div style="color:#0071e3; font-size:12px; font-weight:700; margin-bottom:8px;">DESIGN CASE {i+1}</div>
                    <div style="font-size:18px; font-weight:600; margin-bottom:4px;">{sty}风格 - {s}</div>
                    <div style="font-size:14px; opacity:0.7; margin-bottom:12px;">建议部位：{p} | 呈现氛围：{v}</div>
                    <div style="background:rgba(0,113,227,0.05); padding:12px; border-radius:8px; font-size:12px; font-family:monospace; border: 1px solid rgba(0,113,227,0.1);">
                        Prompt: {s}, {sty} tattoo style, {v}, on {p}, white background, high detail
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("零件库不完整！请确保“主体、风格、部位、氛围”四个库里都有内容。")
