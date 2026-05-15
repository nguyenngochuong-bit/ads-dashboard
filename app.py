import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Ads Reporter", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1a1f3a; }
[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def gen_data(days=30):
    dates = pd.date_range(end=datetime.today(), periods=days)
    np.random.seed(42)
    return pd.DataFrame({
        "Ngày": dates,
        "Chi phí": np.random.randint(8_000_000, 16_000_000, days),
        "Clicks": np.random.randint(5000, 12000, days),
        "Impressions": np.random.randint(200_000, 400_000, days),
        "Conversions": np.random.randint(100, 300, days),
    })

@st.cache_data
def gen_campaigns():
    names = ["Brand Awareness Q2", "Lead Gen - Khóa học", "Retargeting Web", "TikTok Viral May", "Search - Competitor"]
    np.random.seed(1)
    return pd.DataFrame({
        "Tên chiến dịch": names,
        "Chi phí (đ)": [f"{x:,}" for x in np.random.randint(5_000_000, 20_000_000, 5)],
        "Clicks": np.random.randint(1000, 8000, 5),
        "CTR (%)": np.round(np.random.uniform(1.2, 4.5, 5), 2),
        "CPC (đ)": [f"{x:,}" for x in np.random.randint(3000, 12000, 5)],
        "Chuyển đổi": np.random.randint(20, 150, 5),
        "ROAS": np.round(np.random.uniform(2.0, 6.5, 5), 2),
    })

with st.sidebar:
    st.markdown("## 📊 Ads Reporter")
    st.markdown("---")
    platform = st.radio("Nền tảng", ["Google Ads", "Meta Ads", "TikTok Ads", "GA4 Analytics"])
    st.markdown("---")
    account_id = st.text_input("AD ACCOUNT ID", placeholder="123-456-7890")
    demo_mode = st.toggle("Demo data", value=True)
    st.markdown("---")
    st.caption("demo@agency.com")
    st.button("Đăng xuất")

st.title(f"📈 {platform} Dashboard")
st.caption("Tổng quan hiệu suất quảng cáo")

selected_date = st.radio("", ["Hôm nay", "Hôm qua", "Tuần này", "Tháng này", "Quý này"], horizontal=True, index=3)
days_map = {"Hôm nay": 1, "Hôm qua": 2, "Tuần này": 7, "Tháng này": 30, "Quý này": 90}
df = gen_data(days_map[selected_date])

st.markdown("---")

total_spend = df["Chi phí"].sum()
total_clicks = df["Clicks"].sum()
total_impr = df["Impressions"].sum()
total_conv = df["Conversions"].sum()
ctr = round(total_clicks / total_impr * 100, 2)
cpc = round(total_spend / total_clicks)
roas = round(np.random.uniform(3.2, 5.8), 2)

k1,k2,k3,k4,k5,k6,k7 = st.columns(7)
k1.metric("Chi phí", f"{total_spend/1e6:.1f}M đ", "+12.4%")
k2.metric("Clicks", f"{total_clicks:,}", "+8.2%")
k3.metric("Impressions", f"{total_impr/1000:.0f}K", "+15.7%")
k4.metric("Chuyển đổi", f"{total_conv}", "+4.1%")
k5.metric("CTR", f"{ctr}%", "+0.3%")
k6.metric("CPC", f"{cpc:,}đ", "-5.2%")
k7.metric("ROAS", f"{roas}x", "+18.3%")

st.markdown("---")

c1, c2 = st.columns([2, 1])
with c1:
    st.subheader(f"Hiệu suất {days_map[selected_date]} ngày gần nhất")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Ngày"], y=df["Chi phí"], name="Chi phí", fill="tozeroy",
                             line=dict(color="#6366f1", width=2), fillcolor="rgba(99,102,241,0.15)"))
    fig.add_trace(go.Bar(x=df["Ngày"], y=df["Clicks"], name="Clicks", yaxis="y2",
                         marker_color="rgba(16,185,129,0.6)"))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right"),
                      legend=dict(orientation="h"), height=350,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Phân bổ mục tiêu")
    fig2 = px.pie(values=[35,30,20,15], names=["Nhận thức","Chuyển đổi","Lưu lượng","Tương tác"],
                  hole=0.5, color_discrete_sequence=["#6366f1","#8b5cf6","#a78bfa","#c4b5fd"])
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("📋 Hiệu suất theo chiến dịch")
camp_df = gen_campaigns()

_, col1, col2 = st.columns([4,1,1])
with col1:
    st.download_button("📥 CSV", camp_df.to_csv(index=False).encode(), "campaigns.csv", "text/csv")
with col2:
    buf = io.BytesIO()
    camp_df.to_excel(buf, index=False)
    st.download_button("📊 Excel", buf.getvalue(), "campaigns.xlsx")

st.dataframe(camp_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("🤖 Phân tích AI")
if st.button("Phân tích hiệu suất", type="primary"):
    with st.spinner("AI đang phân tích..."):
        import time; time.sleep(2)
    st.success("Phân tích hoàn tất!")
    st.markdown("""
**Executive Summary:**
- 🔴 Campaign "Retargeting Web" CPA cao gấp 2.3x mục tiêu — cần review audience
- 🟡 CTR tổng thể 1.58% thấp hơn benchmark (2.5%) — test creative mới
- 🟢 "Brand Awareness Q2" ROAS 5.2x — tăng budget thêm 20%
- 💡 Thứ 3-4 convert tốt nhất — tập trung budget vào 2 ngày này
    """)
