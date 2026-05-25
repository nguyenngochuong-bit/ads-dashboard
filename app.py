import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Ads Reporter", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebar"] {background-color: #1a1f3a;}
[data-testid="stSidebar"] * {color: white !important;}
.metric-card {background: #1e2139; border-radius: 10px; padding: 16px; text-align: center;}
.metric-value {font-size: 26px; font-weight: bold; color: white;}
.metric-label {font-size: 12px; color: #aaa; margin-bottom: 4px;}
.metric-delta-up {font-size: 11px; color: #59a14f;}
.metric-delta-down {font-size: 11px; color: #e15759;}
</style>
""", unsafe_allow_html=True)


def get_google_ads_client(login_cid=None):
    import requests
    from google.ads.googleads.client import GoogleAdsClient
    from google.oauth2.credentials import Credentials

    cid     = os.environ["GOOGLE_ADS_CLIENT_ID"]
    csecret = os.environ["GOOGLE_ADS_CLIENT_SECRET"]
    rtoken  = os.environ["GOOGLE_ADS_REFRESH_TOKEN"]

    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id":     cid,
            "client_secret": csecret,
            "refresh_token": rtoken,
            "grant_type":    "refresh_token",
        },
        timeout=30,
    )
    data = r.json()
    if "error" in data:
        raise Exception(f"OAuth lỗi: {data['error']} – {data.get('error_description','')}")

    creds = Credentials(
        token=data["access_token"],
        refresh_token=rtoken,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cid,
        client_secret=csecret,
    )
    kwargs = dict(
        credentials=creds,
        developer_token=os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        use_proto_plus=True,
    )
    if login_cid:
        kwargs["login_customer_id"] = login_cid
    return GoogleAdsClient(**kwargs)


def get_google_ads_data(customer_id, days):
    try:
        client = get_google_ads_client(login_cid=None)
        ga_service = client.get_service("GoogleAdsService")
        end_date   = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        query = f"""
            SELECT segments.date, metrics.cost_micros, metrics.clicks,
                   metrics.impressions, metrics.conversions
            FROM customer
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY segments.date
        """
        response = ga_service.search(customer_id=customer_id, query=query)
        rows = []
        for row in response:
            rows.append({
                "Ngày":        row.segments.date,
                "Chi phí":     row.metrics.cost_micros / 1_000_000,
                "Clicks":      row.metrics.clicks,
                "Impressions": row.metrics.impressions,
                "Chuyển đổi": row.metrics.conversions,
            })
        return pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.error(f"Lỗi Google Ads API (data): {str(e)}")
        return None


def get_google_ads_campaigns(customer_id):
    try:
        client = get_google_ads_client(login_cid=None)
        ga_service = client.get_service("GoogleAdsService")
        query = """
            SELECT campaign.name, metrics.cost_micros, metrics.clicks,
                   metrics.ctr, metrics.average_cpc, metrics.conversions,
                   metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_30_DAYS
            ORDER BY metrics.cost_micros DESC LIMIT 10
        """
        response = ga_service.search(customer_id=customer_id, query=query)
        rows = []
        for row in response:
            cost       = row.metrics.cost_micros / 1_000_000
            conv_value = row.metrics.conversions_value
            rows.append({
                "Chiến dịch":  row.campaign.name,
                "Chi phí":     cost,
                "Clicks":      row.metrics.clicks,
                "CTR":         f"{row.metrics.ctr*100:.2f}%",
                "CPC":         f"{row.metrics.average_cpc/1_000_000:,.0f}đ",
                "Chuyển đổi": f"{row.metrics.conversions:.0f}",
                "ROAS":        f"{conv_value/cost:.1f}x" if cost > 0 else "N/A",
            })
        return pd.DataFrame(rows) if rows else None
    except Exception as e:
        st.error(f"Lỗi Google Ads API (campaigns): {str(e)}")
        return None


def get_mock_data(days):
    np.random.seed(42)
    dates = [(datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d")
             for i in range(days, 0, -1)]
    return pd.DataFrame({
        "Ngày":        dates,
        "Chi phí":     np.random.uniform(5_000_000, 15_000_000, days),
        "Clicks":      np.random.randint(500, 2000, days),
        "Impressions": np.random.randint(10_000, 50_000, days),
        "Chuyển đổi": np.random.uniform(5, 30, days),
    })


def get_mock_campaigns():
    np.random.seed(42)
    names = ["Brand Search", "Performance Max", "Display Remarketing",
             "Video Awareness", "Shopping"]
    costs  = np.random.uniform(10_000_000, 80_000_000, 5)
    clicks = np.random.randint(1000, 15000, 5)
    convs  = np.random.uniform(10, 200, 5)
    rows = []
    for i in range(5):
        c = costs[i]
        rows.append({
            "Chiến dịch":  names[i],
            "Chi phí":     f"{c/1_000_000:.1f}M đ",
            "Clicks":      f"{clicks[i]:,}",
            "CTR":         f"{np.random.uniform(1,5):.2f}%",
            "CPC":         f"{c/clicks[i]:,.0f}đ",
            "Chuyển đổi": f"{convs[i]:.0f}",
            "ROAS":        f"{(convs[i]*500_000)/c:.1f}x",
        })
    return pd.DataFrame(rows)


with st.sidebar:
    st.markdown("## 📊 Ads Reporter")
    st.markdown("---")
    st.markdown("**Nền tảng**")
    platform = st.radio("", ["Google Ads", "Meta Ads", "TikTok Ads", "GA4 Analytics"],
                        label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**AD ACCOUNT ID**")
    customer_id = st.text_input("", value="7569467837", label_visibility="collapsed")
    st.markdown("---")
    use_demo = st.toggle("Demo data", value=False)
    st.markdown("---")
    if st.button("🔍 Test API access"):
        try:
            c = get_google_ads_client(login_cid=None)
            cs = c.get_service("CustomerService")
            res = cs.list_accessible_customers()
            ids = [r.split("/")[1] for r in res.resource_names]
            st.success("Accounts: " + ", ".join(ids))
        except Exception as e:
            st.error(str(e)[:400])
    st.markdown("---")
    st.markdown("demo@agency.com")
    st.button("Đăng xuất")


days_map = {"Hôm nay": 1, "Hôm qua": 2, "Tuần này": 7, "Tháng này": 30, "Quý này": 90}

st.markdown("## 📈 Google Ads Dashboard")
st.caption("Tổng quan hiệu suất quảng cáo")

period = st.radio("", list(days_map.keys()), index=3, horizontal=True,
                  label_visibility="collapsed")
days = days_map[period]

if use_demo or platform != "Google Ads":
    df           = get_mock_data(days)
    df_campaigns = get_mock_campaigns()
    if not use_demo and platform != "Google Ads":
        st.info(f"{platform} chưa được tích hợp – đang dùng demo data.")
else:
    with st.spinner("Đang tải dữ liệu từ Google Ads..."):
        df           = get_google_ads_data(customer_id, days)
        df_campaigns = get_google_ads_campaigns(customer_id)
    if df is None:
        st.warning("Không lấy được data thật – dùng demo data.")
        df           = get_mock_data(days)
        df_campaigns = get_mock_campaigns()

total_cost   = df["Chi phí"].sum()
total_clicks = int(df["Clicks"].sum())
total_impr   = int(df["Impressions"].sum())
total_conv   = df["Chuyển đổi"].sum()
ctr  = total_clicks / total_impr * 100 if total_impr > 0 else 0
cpc  = total_cost / total_clicks       if total_clicks > 0 else 0
roas = (total_conv * 500_000) / total_cost if total_cost > 0 else 0

metrics = [
    ("Chi phí",     f"{total_cost/1_000_000:.1f}M đ", "+12.4%", True),
    ("Clicks",      f"{total_clicks:,}",               "+8.2%",  True),
    ("Impressions", f"{total_impr/1000:.0f}K",         "+15.7%", True),
    ("Chuyển đổi", f"{total_conv:,.0f}",               "+4.1%",  True),
    ("CTR",         f"{ctr:.2f}%",                     "+0.3%",  True),
    ("CPC",         f"{cpc:,.0f}đ",                    "-5.2%",  False),
    ("ROAS",        f"{roas:.2f}x",                    "+18.3%", True),
]

cols = st.columns(7)
for col, (label, value, delta, up) in zip(cols, metrics):
    delta_class = "metric-delta-up" if up else "metric-delta-down"
    arrow = "↑" if up else "↓"
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="{delta_class}">{arrow} {delta}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_l, col_r = st.columns(2)

with col_l:
    st.markdown("### Hiệu suất gần nhất")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Ngày"], y=df["Chi phí"],
                         name="Chi phí", marker_color="#4e79a7", opacity=0.85))
    fig.add_trace(go.Scatter(x=df["Ngày"], y=df["Clicks"] * 5000,
                             name="Clicks", line=dict(color="#f28e2b", width=2),
                             yaxis="y2"))
    fig.update_layout(
        paper_bgcolor="#1e2139", plot_bgcolor="#1e2139",
        font=dict(color="white", size=11),
        yaxis=dict(gridcolor="#2e3460", title="Chi phí (đ)"),
        yaxis2=dict(overlaying="y", side="right", showgrid=False),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=320, margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown("### Phân bổ mục tiêu")
    fig2 = go.Figure(go.Pie(
        labels=["Brand", "Performance", "Display", "Video"],
        values=[30, 40, 20, 10], hole=0.55,
        marker=dict(colors=["#4e79a7", "#f28e2b", "#59a14f", "#e15759"]),
    ))
    fig2.update_layout(
        paper_bgcolor="#1e2139", font=dict(color="white"),
        height=320, margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Top chiến dịch (30 ngày gần nhất)")
if df_campaigns is not None and not df_campaigns.empty:
    st.dataframe(df_campaigns, use_container_width=True, hide_index=True)
else:
    st.info("Không có dữ liệu chiến dịch.")
