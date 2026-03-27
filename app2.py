import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# 页面配置
st.set_page_config(page_title="心跳包监控仪表板", page_icon="❤️", layout="wide")

# 自定义样式
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-weight: 600; }
    .metric-card {
        background-color: rgba(27, 31, 35, 0.05);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid rgba(27, 31, 35, 0.15);
    }
    @media (prefers-color-scheme: dark) {
        .metric-card { background-color: rgba(255, 255, 255, 0.07); border-color: rgba(255, 255, 255, 0.15); }
    }
</style>
""", unsafe_allow_html=True)

# 生成模拟数据
def generate_heartbeat_data(duration_seconds=120, sample_rate_hz=2):
    total_points = duration_seconds * sample_rate_hz
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=duration_seconds)
    timestamps = pd.date_range(start=start_time, end=end_time, periods=total_points)
    
    base_seq = np.arange(1, total_points + 1)
    noise = np.random.normal(0, 0.3, total_points).cumsum() * 0.2
    jumps = np.zeros(total_points)
    num_jumps = np.random.randint(2, 6)
    jump_indices = np.random.choice(total_points - 1, num_jumps, replace=False)
    for idx in jump_indices:
        jumps[idx:] += np.random.randint(3, 15)
    sequence = base_seq + noise + jumps
    sequence = np.maximum.accumulate(sequence)
    sequence = np.round(sequence, 1)
    
    return pd.DataFrame({'timestamp': timestamps, 'heartbeat_seq': sequence})

def main():
    # 标题与GitHub徽章
    col_title, col_github = st.columns([3, 1])
    with col_title:
        st.title("❤️ 心跳包实时监控")
        st.markdown("基于 **Streamlit** 构建 | 心跳包序号随时间变化趋势")
    with col_github:
        st.markdown("""
        <div style="text-align: right; padding-top: 1rem;">
            <a href="https://github.com" target="_blank">
                <img src="https://img.shields.io/badge/GitHub-源码仓库-181717?style=flat&logo=github">
            </a>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 数据控制")
        duration = st.slider("数据时长 (秒)", 30, 300, 120, 10)
        sample_rate = st.slider("采样频率 (包/秒)", 1, 10, 2, 1)
        regenerate = st.button("🔄 重新生成数据", use_container_width=True)

    # 数据生成/更新
    if 'df' not in st.session_state or regenerate:
        with st.spinner("生成心跳包数据..."):
            st.session_state.df = generate_heartbeat_data(duration, sample_rate)
    df = st.session_state.df

    # 关键指标
    latest_seq = df['heartbeat_seq'].iloc[-1]
    first_seq = df['heartbeat_seq'].iloc[0]
    total_packets = len(df)
    time_span = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds()
    avg_rate = total_packets / time_span if time_span else 0
    seq_growth = latest_seq - first_seq

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最新心跳序号", f"{latest_seq:.1f}", f"+{seq_growth:.1f}")
    c2.metric("总心跳包数量", f"{total_packets:,}")
    c3.metric("平均发送频率", f"{avg_rate:.2f} 包/秒")
    c4.metric("时间跨度", f"{time_span:.0f} 秒")
    st.divider()

    # 折线图（matplotlib）
    st.subheader("📈 心跳包序号时间序列")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['timestamp'], df['heartbeat_seq'], 
            color='#e25555', linewidth=2, marker='o', markersize=2, label='心跳序号')
    ax.set_xlabel("时间戳")
    ax.set_ylabel("心跳包序号")
    ax.set_title("心跳包序号随时间演化趋势")
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    # 增量分析
    st.subheader("📊 序号增量分析")
    df['delta'] = df['heartbeat_seq'].diff().fillna(0)
    delta_pos = df[df['delta'] > 0]['delta'].values

    col_hist, col_stats = st.columns([2, 1])
    with col_hist:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.hist(delta_pos, bins=30, color='#58a6ff', alpha=0.7, edgecolor='black')
        ax2.set_title("相邻心跳包序号增量分布")
        ax2.set_xlabel("序号增量")
        ax2.set_ylabel("频次")
        st.pyplot(fig2)
    with col_stats:
        st.markdown("### 📐 统计摘要")
        if len(delta_pos) > 0:
            stats = {
                "均值": f"{np.mean(delta_pos):.3f}",
                "中位数": f"{np.median(delta_pos):.3f}",
                "标准差": f"{np.std(delta_pos):.3f}",
                "最小值": f"{np.min(delta_pos):.3f}",
                "最大值": f"{np.max(delta_pos):.3f}",
                "95%分位数": f"{np.percentile(delta_pos, 95):.3f}"
            }
            for k, v in stats.items():
                st.markdown(f"**{k}:** `{v}`")
        else:
            st.info("无有效增量数据")
        st.caption("💡 模拟了网络抖动与突发跳跃，增量可能大于1。")

    # 数据表
    with st.expander("📋 原始数据表", expanded=False):
        st.dataframe(df[['timestamp', 'heartbeat_seq', 'delta']].round(2), use_container_width=True)

if __name__ == "__main__":
    main()
