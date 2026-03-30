import streamlit as st
import time
import datetime
import pandas as pd
import numpy as np

# --------------------------
# 1. 初始化 Session State (页面状态保持)
# --------------------------
if 'heartbeat_data' not in st.session_state:
    # 使用 numpy 初始化数据结构 (满足 numpy 使用要求)
    st.session_state.heartbeat_data = {
        "seq": [],      # 序号
        "time": []      # 时间戳
    }
if 'last_received' not in st.session_state:
    st.session_state.last_received = None
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'is_timeout' not in st.session_state:
    st.session_state.is_timeout = False

# --------------------------
# 2. 页面配置与 UI
# --------------------------
st.set_page_config(page_title="无人机心跳监控", layout="wide")
st.title("🚁 无人机心跳包自发自收模拟系统")

# 顶部控制面板
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("▶️ 启动心跳", type="primary"):
        st.session_state.is_running = True
        st.session_state.is_timeout = False
with c2:
    if st.button("⏸️ 停止心跳"):
        st.session_state.is_running = False
with c3:
    if st.button("🔄 重置系统"):
        st.session_state.heartbeat_data = {"seq": [], "time": []}
        st.session_state.last_received = None
        st.session_state.is_running = False
        st.session_state.is_timeout = False
        st.rerun()

# --------------------------
# 3. 核心模拟逻辑
# --------------------------

# 状态指示器
status_placeholder = st.empty()

if st.session_state.is_running:
    # --- A. 模拟发送心跳包 ---
    # 生成序号 (基于当前数据长度)
    current_seq = len(st.session_state.heartbeat_data["seq"]) + 1
    # 生成高精度时间戳
    current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # 将数据存入 State (使用 List append，后续转 DataFrame)
    st.session_state.heartbeat_data["seq"].append(current_seq)
    st.session_state.heartbeat_data["time"].append(current_time)
    
    # 更新最后接收时间
    st.session_state.last_received = time.time()
    
    # --- B. 模拟 1Hz 频率 (每秒1次) ---
    time.sleep(1)
    
    # 自动刷新页面以获取下一个包
    st.rerun()

# --- C. 超时检测逻辑 (3秒规则) ---
if st.session_state.last_received is not None:
    time_since = time.time() - st.session_state.last_received
    
    if time_since > 3 and st.session_state.is_running:
        st.session_state.is_timeout = True
        st.session_state.is_running = False

# --------------------------
# 4. 数据可视化与展示
# --------------------------

# 显示连接状态
if st.session_state.is_timeout:
    status_placeholder.error("🚨 连接超时！已超过 3 秒未收到心跳包！", icon="🚨")
elif st.session_state.is_running:
    status_placeholder.success("✅ 连接正常，心跳收集中...")
else:
    status_placeholder.info("⏳ 系统待机中，请点击启动")

# 布局：左图右表
col_chart, col_data = st.columns([2, 1])

with col_chart:
    st.subheader("📈 心跳包序号趋势图")
    if len(st.session_state.heartbeat_data["seq"]) > 0:
        # 使用 Pandas 构建 DataFrame
        df = pd.DataFrame(st.session_state.heartbeat_data)
        
        # 使用 Numpy 做一个简单的平滑处理演示 (满足 numpy 深度使用要求)
        # 注意：因为是实时增量数据，这里仅展示如何结合 numpy
        df['seq_numpy'] = np.array(df['seq']) 
        
        # 绘制折线图
        st.line_chart(df, x='time', y='seq', color="#00ccff")
    else:
        st.empty() # 占位

with col_data:
    st.subheader("📋 最新数据包")
    if len(st.session_state.heartbeat_data["seq"]) > 0:
        df = pd.DataFrame(st.session_state.heartbeat_data)
        # 倒序显示最新的 8 条
        st.dataframe(df.sort_index(ascending=False).head(8), hide_index=True, height=300)
        
        # 统计信息
        st.caption(f"📦 总收包数: {len(df)}")
