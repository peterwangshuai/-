import streamlit as st
import time
import datetime
import pandas as pd
import numpy as np

# --------------------------
# 1. 初始化 Session State
# --------------------------
if 'df_history' not in st.session_state:
    st.session_state.df_history = pd.DataFrame(columns=["time", "seq"])
if 'last_received' not in st.session_state:
    st.session_state.last_received = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'is_timeout' not in st.session_state:
    st.session_state.is_timeout = False

# --------------------------
# 2. 页面配置
# --------------------------
st.set_page_config(page_title="实时心跳监控", layout="wide")
st.title("🚁 无人机心跳包 - 实时动态监控")

# 控制面板
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("▶️ 启动", type="primary"):
        st.session_state.is_running = True
        st.session_state.is_timeout = False
with c2:
    if st.button("⏸️ 暂停"):
        st.session_state.is_running = False
with c3:
    if st.button("🔄 清空重置"):
        st.session_state.df_history = pd.DataFrame(columns=["time", "seq"])
        st.session_state.last_received = None
        st.session_state.is_running = False
        st.session_state.is_timeout = False
        st.rerun()

# 状态显示区
status_box = st.empty()
# 注意：这里不再预先 empty() 占位图表，而是直接在下方画
st.subheader("📈 实时趋势图")
chart_placeholder = st.empty() 
st.subheader("📋 最新数据包")
data_box = st.empty()

# --------------------------
# 3. 核心逻辑循环
# --------------------------

# 先初始化图表对象 (关键修复点)
# 如果有历史数据，先画上；没有就画个空的
if len(st.session_state.df_history) > 0:
    chart_obj = chart_placeholder.line_chart(
        st.session_state.df_history, 
        x="time", 
        y="seq", 
        color="#39ff14"
    )
else:
    # 初始化一个空图表对象
    chart_obj = chart_placeholder.line_chart(pd.DataFrame(columns=["time", "seq"]), x="time", y="seq")

while st.session_state.is_running:
    # --- 1. 生成新的心跳数据 ---
    current_seq = len(st.session_state.df_history) + 1
    current_time_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    new_data = pd.DataFrame({
        "time": [current_time_str],
        "seq": [current_seq]
    })
    
    # --- 2. 追加到历史数据 ---
    st.session_state.df_history = pd.concat(
        [st.session_state.df_history, new_data], 
        ignore_index=True
    )
    
    # --- 3. 实时更新图表 (修复后的正确用法) ---
    # 直接对保存好的 chart_obj 使用 add_rows
    chart_obj.add_rows(new_data)
    
    # --- 4. 更新状态和表格 ---
    status_box.success(f"✅ 连接正常 | 最新序号: {current_seq} | 时间: {current_time_str}")
    
    data_box.dataframe(
        st.session_state.df_history.sort_index(ascending=False).head(10), 
        hide_index=True, 
        height=300
    )
    
    # --- 5. 超时检测预备 ---
    st.session_state.last_received = time.time()
    
    # --- 6. 模拟 1Hz 频率 ---
    time.sleep(1)

# --------------------------
# 4. 非运行状态下的显示
# --------------------------

if st.session_state.last_received is not None and not st.session_state.is_running:
    elapsed = time.time() - st.session_state.last_received
    if elapsed > 3 and len(st.session_state.df_history) > 0:
        status_box.error("🚨 【警报】连接超时！超过 3 秒未收到心跳包！", icon="🚨")
    elif len(st.session_state.df_history) > 0:
        status_box.warning("⏸️  已暂停")
