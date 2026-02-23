import streamlit as st
import pandas as pd
import openpyxl
from openpyxl import load_workbook
from openai import OpenAI
import plotly.express as px
from io import BytesIO
from datetime import datetime

# --- 1. 初始化配置 ---
st.set_page_config(page_title="AI 审计终端 V12.3", page_icon="🧼", layout="wide")

for key in ["logged_in", "df_cleaned", "messages", "current_file", "raw_binary"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else None
if "messages" not in st.session_state: st.session_state["messages"] = []

# --- 2. 视觉引擎：颜色识别与提取 ---
def process_visual_data(file_bytes, mode="all"):
    """
    mode "uncolored": 仅提取没颜色的
    mode "colored": 仅提取标记了颜色的
    """
    wb = load_workbook(BytesIO(file_bytes), data_only=True)
    ws = wb.active
    extracted_data = []
    
    for row in ws.iter_rows(min_row=1):
        cell = row[0] # 默认检查第一列 A列
        fill = cell.fill
        # 识别颜色逻辑：'00000000' 或索引 64/0 通常代表无填充
        is_colored = fill.start_color.index not in ['00000000', 0, 64] and fill.fill_type is not None
        
        val = cell.value
        if val is not None:
            if mode == "uncolored" and not is_colored:
                extracted_data.append(val)
            elif mode == "colored" and is_colored:
                extracted_data.append(val)
            elif mode == "all":
                extracted_data.append(val)
                
    # 转换为 DataFrame 方便展示，由于是纯数字，自动命名为“号码库”
    return pd.DataFrame(extracted_data, columns=["号码库"])

# --- 3. 物理清洗引擎：生成干净的 Excel ---
def export_cleaned_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=True)
    return output.getvalue()

# --- 4. 侧边栏：清洗控制台 ---
with st.sidebar:
    st.title("🧼 数据清洗站")
    uploaded_file = st.file_uploader("📂 上传您的表格 (xlsx)", type=["xlsx"])
    
    if uploaded_file:
        st.session_state["raw_binary"] = uploaded_file.read()
        st.session_state["current_file"] = uploaded_file.name
        
        st.divider()
        st.subheader("🛠️ 视觉过滤选项")
        filter_mode = st.radio("提取范围：", ["全部提取", "仅提取未标记颜色", "仅提取已标记颜色"])
        
        mode_map = {"全部提取": "all", "仅提取未标记颜色": "uncolored", "仅提取已标记颜色": "colored"}
        
        if st.button("🚀 执行视觉提取", use_container_width=True):
            with st.spinner("正在扫描单元格颜色..."):
                st.session_state["df_cleaned"] = process_visual_data(
                    st.session_state["raw_binary"], 
                    mode=mode_map[filter_mode]
                )
            st.success("提取完成！")

    if st.session_state["df_cleaned"] is not None:
        st.divider()
        st.subheader("📥 成果导出")
        # 导出清洗后的 Excel
        clean_xlsx = export_cleaned_excel(st.session_state["df_cleaned"])
        st.download_button(
            label="💾 下载清洗后的 Excel",
            data=clean_xlsx,
            file_name=f"已清洗_{datetime.now().strftime('%H%m%s')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

# --- 5. 主界面：审计与对话 ---
st.title("📊 AI 自动化办公看板 V12.3")

if st.session_state["df_cleaned"] is not None:
    df = st.session_state["df_cleaned"]
    
    tab_data, tab_ai = st.tabs(["💎 数据预览", "🤖 AI 深度诊断"])
    
    with tab_data:
        st.write(f"已为您提取 {len(df)} 条记录")
        st.dataframe(df, use_container_width=True)
        # 简单统计
        if not df.empty:
            st.info(f"💡 发现 {df.duplicated().sum()} 条重复记录")

    with tab_ai:
        OFFICIAL_KEY = st.secrets.get("DEEPSEEK_API_KEY")
        if OFFICIAL_KEY:
            client = OpenAI(api_key=OFFICIAL_KEY, base_url="https://api.deepseek.com")
            
            for msg in st.session_state["messages"]:
                with st.chat_message(msg["role"]): st.write(msg["content"])
                if user_input := st.chat_input("您可以问：这些没标记颜色的号里有多少重复的？"):
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"): st.write(user_input)
                
                with st.chat_message("assistant"):
                    # 喂给 AI 提取出的数据片段
                    context = f"当前提取的数据前30行：\n{df.head(30).to_string()}\n总记录数：{len(df)}"
                    response = st.write_stream(client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": f"你是审计专家。{context}"},
                            {"role": "user", "content": user_input}
                        ],
                        stream=True
                    ))
                st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.warning("请配置 API Key 以启用 AI 诊断。")
else:
    st.info("👋 欢迎！请在左侧上传 Excel 文件并选择提取模式。")