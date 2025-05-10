
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# لاگین
def login():
    st.title("ورود به داشبرد فروش جاباما")
    username = st.text_input("نام کاربری")
    password = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        valid_users = {
            "admin": "1234",
            "Kazemi": "ghasemi",
            "Soltani": "Golnaz"
        }
        if username in valid_users and password == valid_users[username]:
            st.session_state.logged_in = True
        else:
            st.error("نام کاربری یا رمز عبور نادرست است")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    login()
    st.stop()

st.set_page_config(page_title="Jabama Full Dashboard", layout="wide")
st.title("داشبورد نهایی مانیتورینگ دایرکت - جاباما")

uploaded_file = st.file_uploader("فایل خروجی نوین‌هاب را بارگذاری کنید (Excel)", type=["xlsx"])

def classify_sla(sla):
    if sla <= 10:
        return '0-10 دقیقه'
    elif sla <= 20:
        return '10-20 دقیقه'
    elif sla <= 30:
        return '20-30 دقیقه'
    elif sla <= 40:
        return '30-40 دقیقه'
    elif sla <= 60:
        return '40-60 دقیقه'
    else:
        return '60+ دقیقه'

def show_sla_distribution_table(df):
    st.subheader("درصد پاسخ‌گویی کارشناسان در بازه‌های زمانی مختلف SLA (به ازای اکانت)")
    selected_account = st.selectbox("انتخاب اکانت برای مشاهده توزیع SLA", df['account'].dropna().unique())
    df_filtered = df[df['account'] == selected_account].dropna(subset=['sla', 'responded_from'])
    df_filtered['SLA Range'] = df_filtered['sla'].apply(classify_sla)
    dist = pd.crosstab(index=df_filtered['SLA Range'],
                       columns=df_filtered['responded_from'],
                       normalize='columns') * 100
    dist = dist.reindex(['0-10 دقیقه', '10-20 دقیقه', '20-30 دقیقه', '30-40 دقیقه', '40-60 دقیقه', '60+ دقیقه'])
    st.dataframe(dist.style.format("{:.1f}%"))

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.rename(columns={
        'Date': 'date',
        'Username': 'user',
        'Type': 'type',
        'Text': 'text',
        'Account': 'account',
        'Status': 'status',
        'Responder': 'responded_from',
        'Tag': 'tag'
    })

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values('date')
    df['hour'] = df['date'].dt.hour
    df['day'] = df['date'].dt.date

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    start_date, end_date = st.date_input("بازه تاریخ", [min_date, max_date], min_value=min_date, max_value=max_date)
    df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

    st.subheader("آمار کلی")
    col1, col2, col3 = st.columns(3)
    col1.metric("کل پیام‌ها", len(df))
    col2.metric("تعداد اکانت‌ها", df['account'].nunique())
    col3.metric("کاربران یکتا", df['user'].nunique())

    
    st.subheader("خلاصه وضعیت TTFT")
    if 'sla' in df.columns:
        max_sla_row = df.dropna(subset=['sla']).sort_values('sla', ascending=False).iloc[0]
        max_sla_account = max_sla_row['account']
        max_sla_value = round(max_sla_row['sla'], 1)
        avg_sla = round(df['sla'].mean(), 1)
        delayed_over_60 = df[df['sla'] > 60].shape[0]

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("بیشترین TTFT مربوط به", max_sla_account, f"{max_sla_value} دقیقه")
        col_b.metric("میانگین TTFT", f"{avg_sla} دقیقه")
        col_c.metric("تعداد پیام با تأخیر بیش از ۱ ساعت", delayed_over_60)

    st.subheader("پیام‌ها به ازای اکانت")
    st.bar_chart(df['account'].value_counts())

    st.subheader("وضعیت پاسخ‌گویی")
    st.bar_chart(df['status'].value_counts())

    st.subheader("پاسخ‌ها به ازای ادمین")
    st.bar_chart(df['responded_from'].value_counts())

    st.subheader("نوع پیام‌ها (type)")
    st.bar_chart(df['type'].value_counts())

    st.subheader("نمایش جدول کامل داده‌ها")
    st.dataframe(df)

    st.divider()
    st.subheader("تحلیل TTFT (زمان پاسخ)")

    # محاسبه SLA
    df['next_date'] = df['date'].shift(-1)
    df['next_user'] = df['user'].shift(-1)
    df['sla'] = (df['next_date'] - df['date']).dt.total_seconds() / 60
    df.loc[df['user'] != df['next_user'], 'sla'] = None

    
    # محاسبه SLA
    df['next_date'] = df['date'].shift(-1)
    df['next_user'] = df['user'].shift(-1)
    df['sla'] = (df['next_date'] - df['date']).dt.total_seconds() / 60
    df.loc[df['user'] != df['next_user'], 'sla'] = None

    # جدول خلاصه SLA
    st.subheader("خلاصه وضعیت TTFT")
    if 'sla' in df.columns:
        max_sla_row = df.dropna(subset=['sla']).sort_values('sla', ascending=False).iloc[0]
        max_sla_account = max_sla_row['account']
        max_sla_value = round(max_sla_row['sla'], 1)
        avg_sla = round(df['sla'].mean(), 1)
        delayed_over_60 = df[df['sla'] > 60].shape[0]

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("بیشترین TTFT مربوط به", max_sla_account, f"{max_sla_value} دقیقه")
        col_b.metric("میانگین TTFT", f"{avg_sla} دقیقه")
        col_c.metric("تعداد پیام با تأخیر بیش از ۱ ساعت", delayed_over_60)

    st.subheader("TTFT ساعتی - کل")
    hourly_sla = df.dropna(subset=['sla']).groupby(df['date'].dt.hour)['sla'].mean().reindex(range(24), fill_value=0)
    st.line_chart(hourly_sla)

    st.subheader("TTFT ساعتی - به ازای اکانت")
    selected_sla_account = st.selectbox("انتخاب اکانت برای نمودار SLA ساعتی", df['account'].dropna().unique(), key="sla_hourly_acc")
    df_selected_acc = df[df['account'] == selected_sla_account]
    hourly_sla_acc = df_selected_acc.dropna(subset=['sla']).groupby(df_selected_acc['date'].dt.hour)['sla'].mean().reindex(range(24), fill_value=0)
    st.line_chart(hourly_sla_acc)

    st.subheader("میانگین TTFT به ازای اکانت و ادمین ")
    sla_summary = df.dropna(subset=['sla']).groupby(['responded_from', 'account'])['sla'].mean().reset_index()
    styled_sla = sla_summary.rename(columns={
        "responded_from": "ادمین",
        "account": "اکانت",
        "sla": "میانگین TTFT (دقیقه)"
    })
    styled_sla_display = styled_sla.style.applymap(
        lambda x: 'background-color: #fdd' if isinstance(x, float) and x > 10 else '',
        subset=["میانگین TTFT (دقیقه)"]
    )
    st.dataframe(styled_sla_display)

    show_sla_distribution_table(df)

    st.subheader("جدول وضعیت پیام‌ها به تفکیک وضعیت به ازای اکانت")
    status_table = df.pivot_table(index='account', columns='status', aggfunc='size', fill_value=0)
    st.dataframe(status_table)

    st.subheader("تعداد پیام‌های شامل کلمه 'قیمت' به ازای هر اکانت")
    df_price = df[df['text'].astype(str).str.contains("قیمت", case=False, na=False)]
    price_table = df_price.groupby('account').size().reset_index(name='تعداد پیام‌های شامل قیمت')
    st.dataframe(price_table)

else:
    st.info("لطفاً فایل خروجی اکسل نوین‌هاب را بارگذاری کنید.")
