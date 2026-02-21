import streamlit as st
import pandas as pd
from openai import OpenAI
import plotly.express as px
from datetime import datetime
from docx import Document  # 📝 新引入：Word文档生成库
from io import BytesIO

# --- 1. 核心配置 ---
st.set_page_config(page_title="AI 智能审计终端 V12.0", page_icon="📝", layout="wide")

for key in ["logged_in", "df_cleaned", "messages", "current_file"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else ([] if key == "messages" else None)

# --- 2. 【新增】Word报告生成引擎 ---
def generate_report(df, alerts, ai_summary):
    doc = Document()
    doc.add_heading('数据智能审计分析报告', 0)
    
    # 基本信息
    doc.add_heading('一、审计基本信息', level=1)
    doc.add_paragraph(f"审计时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph(f"分析样本量：{len(df)} 条记录")
    
    # 风险列表
    doc.add_heading('二、自动扫描发现的风险', level=1)
    if alerts:
        for alert in alerts:
            doc.add_paragraph(alert, style='List Bullet')
    else:
        doc.add_paragraph("未发现基础逻辑错误。")
        
    # AI 专家诊断
    doc.add_heading('三、AI 专家详细建议', level=1)
    doc.add_paragraph(ai_summary if ai_summary else "暂无 AI 诊断记录。")
    
    doc.add_paragraph("\n\n报告由 AI 智能审计终端自动生成。")
    
    # 将文件保存到内存中供下载
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. 自动化审计逻辑 (沿用 V11.4 稳定版) ---
def audit_data(df):
    alerts = []
    if df is None or df.empty: return alerts
    if "联系电话" in df.columns:
        invalid = df[df["联系电话"].astype(str).str.len() != 11]
        if not invalid.empty: alerts.append(f"❌ {len(invalid)} 个电话号码格式异常")
    if "预产期" in df.columns:
        today = datetime.now().strftime("%Y-%m-%d")
        past = df[df["预产期"].astype(str) < today]
        if not past.empty: alerts.append(f"🚩 提醒：有 {len(past)} 条记录预产期早于今天")
    dups = df.duplicated().sum()
    if dups > 0: alerts.append(f"🧬 发现 {dups} 条完全重复的数据记录")
    return alerts

# --- 4. 权限与 AI 初始化 ---
if not st.session_state["logged_in"]:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("🛡️ 审计系统授权")
        invite = st.text_input("演示密钥 (VIP888)", type="password")
        if st.button("解锁进入", use_container_width=True):
            if invite == "VIP888":
                st.session_state["logged_in"] = True
                st.rerun()
    st.stop()

OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")
client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com") if OFFICIAL_KEY else None

# --- 5. 侧边栏 ---
with st.sidebar:
    st.title("⚙️ 审计控制台")
    privacy_mode = st.toggle("🔒 隐私脱敏模式", value=True)
    st.divider()

    # 数据加载
    if st.button("✨ 加载风险演示数据", use_container_width=True):
        st.session_state.update({
            "df_cleaned": pd.DataFrame({
                "姓名": ["张伟", "王芳", "李娜", "陈静", "赵雷", "张伟"],
                "科室": ["内科", "外科", "内科", "儿科", None, "内科"], 
                "预产期": ["2024-01-10", "2025-06-15", "2024-05-09", "2025-08-20", "2024-02-12", "2024-01-10"],
                "联系电话": ["13800138000", "1391234", "13799998888", "13511112222", "18666667777", "13800138000"]
            }),
            "current_file": "Internal_Demo.xlsx", "messages": []
        })
        st.rerun()

    uploaded_file = st.file_uploader("📂 上传业务报表", type=["xlsx", "csv"])
    if uploaded_file and uploaded_file.name != st.session_state["current_file"]:
        st.session_state["df_cleaned"] = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.session_state.update({"current_file": uploaded_file.name, "messages": []})
        st.rerun()

    # 🚀 【核心新增】报告下载按钮
    if st.session_state["df_cleaned"] is not None:
        st.divider()
        st.subheader("📄 成果导出")
        # 准备数据
        current_alerts = audit_data(st.session_state["df_cleaned"])
        last_ai_msg = st.session_state["messages"][-1]["content"] if st.session_state["messages"] else "未进行AI详细诊断"
        doc_bytes = generate_report(st.session_state["df_cleaned"], current_alerts, last_ai_msg)
        st.download_button(
            label="📥 下载 Word 审计报告",
            data=doc_bytes,
            file_name=f"审计报告_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    st.divider()
    if st.button("🚪 退出并清空缓存"):
        st.session_state.clear()
        st.rerun()

# --- 6. 主看板 ---
st.title("📊 AI 自动化办公看板 V12.0")

if st.session_state["df_cleaned"] is not None:
    df = st.session_state["df_cleaned"]
    risk_alerts = audit_data(df)
    for alert in risk_alerts: st.error(alert)

    tab_ai, tab_viz, tab_data = st.tabs(["🤖 AI 专家诊断", "📈 维度分析", "💎 明细看板"])
    
    with tab_ai:
        st.write("### 🤖 首席 AI 审计官")
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        
        if user_input := st.chat_input("询问更多细节..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            with st.chat_message("assistant"):
                context = f"风险：{risk_alerts}\n样表：{df.head().to_string()}"
                response = st.write_stream(client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": f"审计专家，背景：{context}"}, {"role": "user", "content": user_input}],
                    stream=True
                ))
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun() # 为了更新侧边栏的报告内容，刷新一下

    with tab_viz:
        col_x = st.selectbox("选择统计维度", df.columns, index=0)
        plot_data = df[col_x].fillna("（空）").astype(str).value_counts().reset_index()
        plot_data.columns = ['分类', '数量']
        st.plotly_chart(px.bar(plot_data, x='分类', y='数量', color='数量', text_auto=True), use_container_width=True)

    with tab_data:
        display_df = df.copy()
        if privacy_mode:
            for col in display_df.columns:
                if any(x in str(col) for x in ["姓名", "电话", "联系"]):
                    display_df[col] = display_df[col].astype(str).apply(lambda x: x[0] + "*" + x[-1] if len(x)>1 else x)
        st.dataframe(display_df, use_container_width=True)
else:
    st.info("👋 欢迎回来！请在侧边栏上传文件开始工作。")