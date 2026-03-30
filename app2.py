import streamlit as st
import pandas as pd
import numpy as np
import time

# --------------------------
# 1. 初始化会话状态 (Session State)
# --------------------------
if 'heartbeat_data' not in st.session_state:
    # 存储心跳包的 DataFrame
    st.session_state.heartbeat_data = pd.DataFrame(columns=['序号', '时间', '状态'])
    
if 'last_received_time' not in st.session_state:
    # 记录最后一次收到心跳的时间戳
    st.session_state.last_received_time = time.time()
    
if 'sequence' not in st.session_state:
    # 心跳包序号计数器
    st.session_state.sequence = 0

if 'is_timeout' not in st.session_state:
    # 连接状态标志
    st.session_state.is_timeout = False

# --------------------------
# 2. 页面布局配置
# --------------------------
st.set_page_config(page_title="无人机心跳监控", layout="wide")
st.title("🚁 无人机心跳包监控系统")

# 顶部状态栏
status_box = st.empty()

# 左右分栏：左图右表
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("心跳包序号趋势图")
    chart_placeholder = st.empty()

with col2:
    st.subheader("心跳包数据列表")
    table_placeholder = st.empty()

# --------------------------
# 3. 主循环逻辑
# --------------------------
while True:
    current_time = time.time()
    
    # --- 超时检测逻辑 ---
    # 如果当前时间 - 最后一次心跳时间 > 3秒，判定为超时
    if current_time - st.session_state.last_received_time > 3:
        st.session_state.is_timeout = True
    else:
        st.session_state.is_timeout = False
        
        # --- 模拟心跳生成 (自发自收) ---
        # 这里的逻辑是：只要没超时，每秒生成一个新包
        # (为了演示效果，我们不做随机丢包，确保前几个包正常)
        
        st.session_state.sequence += 1
        
        # 格式化时间字符串用于显示
        time_str = time.strftime("%H:%M:%S", time.localtime(current_time))
        
        # 构建新数据行
        new_row = pd.DataFrame({
            '序号': [st.session_state.sequence],
            '时间': [time_str],
            '状态': ['正常']
        })
        
        # 追加到历史数据中
        st.session_state.heartbeat_data = pd.concat(
            [st.session_state.heartbeat_data, new_row], 
            ignore_index=True
        )
        
        # 更新最后接收时间
        st.session_state.last_received_time = current_time

    # --- 界面更新 ---
    
    # 1. 更新顶部状态栏
    with status_box.container():
        if st.session_state.is_timeout:
            st.error(f"❌ 连接超时！已 {current_time - st.session_state.last_received_time:.1f} 秒未收到心跳")
        else:
            st.success("✅ 连接正常")

    # 2. 更新折线图 (仅在有数据时)
    if not st.session_state.heartbeat_data.empty:
        # 为了图表美观，我们将时间作为索引，序号作为值
        df_plot = st.session_state.heartbeat_data.set_index('时间')[['序号']]
        chart_placeholder.line_chart(df_plot, height=300)

    # 3. 更新数据列表 (最新的在最上面)
    with table_placeholder.container():
        st.dataframe(
            st.session_state.heartbeat_data[::-1],  # 倒序显示
            height=300,
            hide_index=True
        )

    # --- 频率控制 ---
    time.sleep(1)
    st.rerun()  # 刷新页面
