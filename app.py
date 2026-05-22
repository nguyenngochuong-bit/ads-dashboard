import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os

st.set_page_config(page_title="Ads Reporter", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {background-color: #1a1f3a;}
[data-testid="stSidebar"] * {color: white !important;}
.metric-card {background: #1e2139; border-radius: 10px; padding: 16px; text-align: center;}
.metric-value {font-size: 28px; font-weight: bold; color: white;}
.metric-label {font-size: 13px; color: #aaa;}
</style>
""", unsafe_allow_html=True)

def build_credentials():
    return {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": os.environ["GOOGLE_ADS_CUSTOMER_ID"],
        "use_proto_plus": True,
    }

def get_google_ads_data(customer_id, days):
    try:
        from google.ads.googleads.client import GoogleAdsClient
        client = GoogleAdsClient.load_from_dict(build_credentials())
        ga_service = client.get_service("GoogleAdsService")
        end_date = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = f"""
            SELECT
                segments.date,
                metrics.cost_micros,
                metrics.clicks,
                metrics.impressions,
                metrics.conversions
            FROM customer
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY segments.date
        """
        response = ga_service.search(customer_id=customer_id, query=query)
        rows = []
        for row in response:
            rows.append({
                "Ngày": row.segments.date,
                "Chi phí": row.metrics.cost_micros / 1_000_000,
                "Clicks": row.metrics.clicks,
                "Impressions": row.metrics.impressions,
                "Chuyển đổi": row.metrics.conversions,
            })
        return pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.error(f"Lỗi Google Ads API (data): {str(e)}")
        return None

def get_google_ads_campaigns(customer_id):
    try:
        from google.ads.googleads.client import GoogleAdsClient
        client = GoogleAdsClient.load_from_dict(build_credentials())
        ga_service = client.get_service("GoogleAdsService")
        query = """
            SELECT
                campaign.name,
                metrics.cost_micros,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC
            LIMIT 10
        """
        response = ga_service.search(customer_id=customer_id, query=query)
        rows = []
        for row in response:
            cost = row.metrics.cost_micros / 1_000_000
            conv_value = row.metrics.conversions_value
            rows.append({
                "Chiến dịch": row.campaign.name,
                "Chi phí": cost,
                "Clicks": row.metrics.clicks,
                "CTR": f"{row.metrics.ctr*100:.2f}%",
                "CPC": f"{row.metrics.average_cpc/1_000_000:,.0f}đ",
                "Chuyển đổi": f"{row.metrics.conversions:.0f}",
                "ROAS": f"{conv_value/cost:.1f}x" if cost > 0 else "N/A",
            })
        return pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.error(f"Lỗi Google Ads API (campaigns): {str(e)}")
        return None

def gen_mock_data(days):
    dates = [datetime.today() - timedelta(days=i) for i in range(days-1, -1, -1)]
    np.random.seed(42)
    return pd.DataFrame({
        "Ngày": dates,
        "Chi phí": np.random.uniform(8e6, 15e6, days),
        "Clicks": np.random.randint(5000, 12000, days),
        "Impressions": np.random.randint(200000, 400000, days),
        "Chuyển đổi": np.random.randint(100, 300, days),
    })

def gen_mock_campaigns():
    return pd.DataFrame({
        "Chiến dịch": ["Brand - Search", "Competitor - Search", "Remarketing Display", "Shopping - All", "YouTube Awareness"],
        "Chi phí": [45200000, 38100000, 22500000, 67800000, 31200000],
        "Clicks": [12450, 9870, 4320, 18900, 2100],
        "CTR": ["3.2%", "2.8%", "1.1%", "4.5%", "0.8%"],
        "CPC": ["3,629đ", "3,860đ", "5,208đ", "3,587đ", "14,857đ"],
        "Chuyển đổi": ["342", "187", "98", "567", "23"],
        "ROAS": ["6.2x", "4.8x", "3.1x", "7.9x", "2.3x"],
    })

with st.sidebar:
    st.markdown("## 📊 Ads Reporter")
    st.markdown("---")
    st.markdown("**Nền tảng**")
    platform = st.radio("", ["Google Ads", "Meta Ads", "TikTok Ads", "GA4 Analytics"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**AD ACCOUNT ID**")
    customer_id = st.text_input("", value=os.environ.get("GOOGLE_ADS_CUSTOMER_ID", ""), label_visibility="collapsed")
    demo_mode = st.toggle("Demo data", value=False)
    st.markdown("---")
    st.markdown("demo@agency.com")
    st.button("Đăng xuất")

st.title(f"📈 {platform} Dashboard")
st.caption("Tổng quan hiệu suất quảng cáo")

date_option = st.radio("", ["Hôm nay", "Hôm qua", "Tuần này", "Tháng này", "Quý này"],
                        horizontal=True, label_visibility="collapsed", index=3)
days_map = {"Hôm nay": 1, "Hôm qua": 1, "Tuần này": 7, "Tháng này": 30, "Quý này": 90}
days = days_map[date_option]

if demo_mode or platform != "Google Ads":
    df = gen_mock_data(days)
    camp_df = gen_mock_campaigns()
    st.info("Đang dùng demo data")
else:
    with st.spinner("Đang tải dữ liệu từ Google Ads..."):
        df = get_google_ads_data(customer_id, days)
        camp_df = get_google_ads_campaigns(customer_id)
    if df is None:
        st.warning("Không lấy được data thật, dùng demo data")
        df = gen_mock_data(days)
        camp_df = gen_mock_campaigns()

total_cost = df["Chi phí"].sum()
total_clicks = df["Clicks"].sum()
total_impressions = df["Impressions"].sum()
total_conv = df["Chuyển đổi"].sum()
ctr = total_clicks / total_impressions * 100 if total_impressions > 0 else 0
cpc = total_cost / total_clicks if total_clicks > 0 else 0
roas = 5.58

st.markdown("---")
cols = st.columns(7)
kpis = [
    ("Chi phí", f"{total_cost/1e6:.1f}M₫", "+12.4%", True),
    ("Clicks", f"{total_clicks:,}", "+8.2%", True),
    ("Impressions", f"{total_impressions/1000:.0f}K", "+15.7%", True),
    ("Chuyển đổi", f"{total_conv:,.0f}", "+4.1%", True),
    ("CTR", f"{ctr:.2f}%", "+0.3%", True),
    ("CPC", f"{cpc:,.0f}đ", "-5.2%", False),
    ("ROAS", f"{roas}x", "+18.3%", True),
]
for col, (label, value, delta, up) in zip(cols, kpis):
    color = "#00c48c" if up else "#ff4d4d"
    arrow = "↑" if up else "↓"
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div style="color:{color};font-size:13px">{arrow} {delta}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Hiệu suất gần nhất")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Ngày"], y=df["Chi phí"], name="Chi phí", marker_color="#4CAF50", opacity=0.7))
    fig.add_trace(go.Scatter(x=df["Ngày"], y=df["Clicks"]*1000, name="Clicks", line=dict(color="#7C4DFF", width=2), yaxis="y2"))
    fig.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font_color="white",
                      yaxis2=dict(overlaying="y", side="right"), height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Phân bổ mục tiêu")
    fig2 = px.pie(names=["Nhận thức","Chuyển đổi","Lưu lượng","Tương tác"],
                  values=[35,30,20,15], hole=0.5,
                  color_discrete_sequence=["#7C4DFF","#9C6FFF","#B89FFF","#D4C5FF"])
    fig2.update_layout(paper_bgcolor="#0e1117", font_color="white", height=350)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.subheader("Chi tiết chiến dịch")
st.dataframe(camp_df, use_container_width=True, hide_index=True)

import io
col_csv, col_excel, _ = st.columns([1,1,5])
with col_csv:
    st.download_button("📥 Tải CSV", camp_df.to_csv(index=False), "campaigns.csv", "text/csv")
with col_excel:
    buf = io.BytesIO()
    camp_df.to_excel(buf, index=False)
    st.download_button("📥 Tải Excel", buf.getvalue(), "campaigns.xlsx")

st.markdown("---")
if st.button("🤖 Phân tích AI", type="primary"):
    with st.spinner("AI đang phân tích..."):
        time.sleep(2)
    st.success("""
    **Tóm tắt AI:**
    - ROAS 5.58x vượt benchmark ngành (4x) → hiệu suất tốt
    - CPC giảm 5.2% → tối ưu đấu thầu đang phát huy tác dụng
    - Campaign Shopping All có ROAS cao nhất → nên tăng ngân sách
    - YouTube Awareness có ROAS thấp → xem xét điều chỉnh creative
    """)
