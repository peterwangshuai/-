import streamlit as st
import time
import datetime
import pandas as pd
import numpy as np
import pydeck as pdk

# --------------------------
# 1. 初始化 Session State（核心数据存储）
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
# 2. 页面基础配置
# --------------------------
st.set_page_config(page_title="无人机心跳+3D地图监控", layout="wide")
st.title("🚁 无人机心跳包 + 3D路径实时监控")

# --------------------------
# 3. 侧边栏：自定义A、B点经纬度
# --------------------------
with st.sidebar:
    st.header("📍 航线坐标设置")
    st.subheader("起点 A")
    a_lat = st.number_input("A点 纬度", value=39.9042, format="%.4f")
    a_lon = st.number_input("A点 经度", value=116.4074, format="%.4f")
    
    st.subheader("终点 B")
    b_lat = st.number_input("B点 纬度", value=31.2304, format="%.4f")
    b_lon = st.number_input("B点 经度", value=121.4737, format="%.4f")
    
    st.caption("默认：北京 → 上海")
    st.divider()

# --------------------------
# 4. 控制面板：启动/暂停/重置
# --------------------------
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("▶️ 启动", type="primary"):
        st.session_state.is_running = True
        st.session_state.is_timeout = False
with c2:
    if st.button("⏸️ 暂停"):
        st.session_state.is_running = False
with c3:
    if st.button("🔄 重置系统"):
        st.session_state.df_history = pd.DataFrame(columns=["time", "seq"])
        st.session_state.last_received = None
        st.session_state.is_running = False
        st.session_state.is_timeout = False
        st.rerun()

# --------------------------
# 5. 界面布局：状态 + 地图 + 图表+数据
# --------------------------
status_box = st.empty()  # 状态提示
map_box = st.empty()     # 3D地图容器

# 下方：左图表 右数据
col_chart, col_data = st.columns([2, 1])
with col_chart:
    st.subheader("📈 心跳包实时趋势")
    chart_placeholder = st.empty()
with col_data:
    st.subheader("📋 最新心跳数据包")
    data_box = st.empty()

# 初始化实时折线图（修复版，无报错）
if len(st.session_state.df_history) > 0:
    chart_obj = chart_placeholder.line_chart(
        st.session_state.df_history, x="time", y="seq", color="#39ff14"
    )
else:
    chart_obj = chart_placeholder.line_chart(pd.DataFrame(columns=["time", "seq"]), x="time", y="seq")

# --------------------------
# 6. 3D地图更新函数（核心）
# --------------------------
def update_map(current_seq, total_steps=50):
    # 计算无人机实时位置（根据心跳序号线性移动）
    progress = min(current_seq / total_steps, 1.0)
    if current_seq == 0:
        progress = 0
        
    drone_lat = a_lat + (b_lat - a_lat) * progress
    drone_lon = a_lon + (b_lon - a_lon) * progress

    # 地图数据
    path_data = [{"path": [[a_lon, a_lat], [b_lon, b_lat]]}]
    point_data = pd.DataFrame({
        "lon": [a_lon, b_lon, drone_lon],
        "lat": [a_lat, b_lat, drone_lat],
        "type": ["起点A", "终点B", "无人机"],
        "color": [[255,0,0], [0,255,0], [255,255,0]]
    })

    # 3D图层
    line_layer = pdk.Layer(
        "ArcLayer", data=path_data, get_path="path",
        get_width=5, get_source_color=[0,0,255], get_target_color=[0,0,255]
    )
    scatter_layer = pdk.Layer(
        "ScatterplotLayer", data=point_data,
        get_position="[lon, lat]", get_color="color", get_radius=20000
    )

    # 相机视角跟随无人机
    view_state = pdk.ViewState(
        latitude=drone_lat, longitude=drone_lon, zoom=4, pitch=50
    )

    # 渲染地图
    r = pdk.Deck(
        layers=[line_layer, scatter_layer], initial_view_state=view_state,
        tooltip={"text": "{type}"}, map_style="mapbox://styles/mapbox/dark-v10"
    )
    map_box.pydeck_chart(r)
    return progress

# --------------------------
# 7. 主循环：心跳+地图+图表同步更新
# --------------------------
# 初始渲染地图
update_map(len(st.session_state.df_history))

while st.session_state.is_running:
    # 生成心跳数据
    current_seq = len(st.session_state.df_history) + 1
    current_time_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    new_data = pd.DataFrame({"time": [current_time_str], "seq": [current_seq]})

    # 保存数据
    st.session_state.df_history = pd.concat([st.session_state.df_history, new_data], ignore_index=True)
    
    # 实时更新图表
    chart_obj.add_rows(new_data)

    # 实时更新3D地图
    progress = update_map(current_seq)

    # 更新状态和数据列表
    status_box.success(f"✅ 正常 | 序号：{current_seq} | 飞行进度：{progress*100:.1f}% | 时间：{current_time_str}")
    data_box.dataframe(st.session_state.df_history.tail(10), hide_index=True, height=250)

    # 记录最后接收时间+延时1秒
    st.session_state.last_received = time.time()
    time.sleep(1)

# --------------------------
# 8. 超时检测（3秒未接收报警）
# --------------------------
if st.session_state.last_received is not None and not st.session_state.is_running:
    elapsed = time.time() - st.session_state.last_received
    if elapsed > 3 and len(st.session_state.df_history) > 0:
        status_box.error("🚨 连接超时！3秒未收到心跳包！")
    else:
        status_box.warning("⏸️ 已暂停")
