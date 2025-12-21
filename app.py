import streamlit as st
from openai import OpenAI
import random

# 配置 DeepSeek
client = OpenAI(api_key='sk-b18b6a62e0374b3ebab3d961c4806a4c', base_url="https://api.deepseek.com")

st.set_page_config(page_title="Tattoo Studio", layout="wide", initial_sidebar_state="collapsed")

# --- 样式逻辑 ---
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
    }
    .res-card {
        background: rgba(128, 128, 128, 0.05);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 核心状态初始化 ---
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}
if 'input_text' not in st.session_state:
    st.session_state.input_text = ""

# --- 定义拆解函数 ---
def handle_disassembly():
    input_val = st.session_state.temp_input # 获取当前输入
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
                        # 自动分类入库
                        if "主体" in k: st.session_state.db["主体"].append(v.strip())
                        elif "风格" in k: st.session_state.db["风格"].append(v.strip())
                        elif "部位" in k: st.session_state.db["部位"].append(v.strip())
                        elif "氛围" in k: st.session_state.db["氛围"].append(v.strip())
                
                # 关键：拆解成功后清空输入框状态
                st.session_state.input_text = "" 
                st.success("分类成功，样板已清理！")
        except Exception as e:
            st.error(f"解析失败: {e}")

# --- 侧边栏 ---
with st.sidebar:
    st.header("📥 素材录入")
    # 使用 value 绑定 session_state，实现自动清空
    st.text_area("样板描述", 
                 value=st.session_state.input_text, 
                 key="temp_input", # 临时存储当前输入
                 placeholder="粘贴描述后点击下方按钮...", 
                 height=150)
    
    # 点击按钮执行函数
    st.button("开始拆解并入库", use_container_width=True, type="primary", on_click=handle_disassembly)

# --- 主界面 ---
st.title("🎨 纹身设计资产看板")

cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]
for i, name in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {name}")
        items = list(set(st.session_state.db[name]))
        if items:
            html_tags = "".join([f'<span class="asset-tag">{x}</span>' for x in items])
            st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{html_tags}</div>', unsafe_allow_html=True)
        else:
            st.caption("暂无数据")

st.markdown("---")
# (下方批量生成逻辑保持不变...)
