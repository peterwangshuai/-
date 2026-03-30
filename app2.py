import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime

# --------------------------
# 1. 初始化 Session State (保持页面刷新后的状态)
# --------------------------
if 'heartbeats' not in st.session_state:
    st.session_state.heartbeats = []  # 存储心跳包数据
if 'last_received_time' not in st.session_state:
    st.session_state.last_received_time = None  # 最后一次收到心跳的时间戳
if 'is_timeout' not in st.session_state:
    st.session_state.is_timeout = False
if 'sequence' not in st.session_state:
    st.session_state.sequence = 0  # 心跳包序号

# --------------------------
# 2. 页面布局
# --------------------------
st.set_page_config(page_title="无人机心跳监控", layout="wide")
st.title("🚁 无人机心跳包监控系统")

# 占位符：用于动态更新内容
status_box = st.empty()
chart_box = st.empty()
data_table_box = st.empty()

# 添加一个开始/停止按钮 (可选，用于控制模拟)
if 'running' not in st.session_state:
    st.session_state.running = True

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("停止模拟" if st.session_state.running else "开始模拟"):
        st.session_state.running = not st.session_state.running
        st.rerun()

# --------------------------
# 3. 主模拟循环
# --------------------------
while st.session_state.running:
    current_ts = time.time()
    current_dt_str = datetime.now().strftime("%H:%M:%S.%f")[:-3] # 格式化时间到毫秒

    # --- A. 模拟发送心跳包 (90% 发送成功率，10% 丢包以模拟超时) ---
    if np.random.rand() < 0.9: 
        st.session_state.sequence += 1
        
        # 构造心跳数据包
        new_heartbeat = {
            "seq": st.session_state.sequence,
            "time_str": current_dt_str,
            "timestamp": current_ts
        }
        
        # 保存数据
        st.session_state.heartbeats.append(new_heartbeat)
        st.session_state.last_received_time = current_ts
        st.session_state.is_timeout = False

    # --- B. 超时检测逻辑 ---
    if st.session_state.last_received_time:
        time_diff = current_ts - st.session_state.last_received_time
        if time_diff > 3:
            st.session_state.is_timeout = True

    # --- C. 更新 UI 界面 ---
    
    # 1. 状态显示
    with status_box.container():
        if st.session_state.is_timeout:
            st.error(f"🔴 **连接超时**！已 {time_diff:.1f} 秒未收到心跳包", icon="🚨")
        else:
            st.success(f"🟢 **连接正常** | 最新序号: {st.session_state.sequence} | 时间: {current_dt_str}")

    # 2. 可视化 (仅当有数据时)
    if st.session_state.heartbeats:
        # 转换为 DataFrame
        df = pd.DataFrame(st.session_state.heartbeats)
        
        # 画折线图 (X:时间字符串, Y:序号)
        with chart_box.container():
            st.subheader("心跳序号趋势图")
            # 使用 Streamlit 原生图表，指定 x 和 y
            st.line_chart(
                data=df, 
                x='time_str', 
                y='seq',
                color="#00cc96",
                x_label="系统时间",
                y_label="心跳包序号"
            )

        # 3. 数据列表 (显示最近 15 条)
        with data_table_box.container():
            st.subheader("原始数据包 (最近 15 条)")
            # 倒序显示，只显示需要的列
            st.dataframe(
                df[['seq', 'time_str']].tail(15).iloc[::-1], 
                hide_index=True,
                use_container_width=True
            )

    # --- D. 控制循环频率 ---
    time.sleep(1)
    st.rerun() # 刷新页面
