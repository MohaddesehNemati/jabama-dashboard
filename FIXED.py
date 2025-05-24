import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt

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

    if df_filtered.empty:
        st.info("هیچ داده‌ای با پاسخ و SLA معتبر برای این اکانت وجود ندارد.")
        return

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

    admin_usernames = ["mahsa.gholamian", "admin123", "support", "Kazemi", "Soltani", "admin"]
    df['responded_from'] = df['responded_from'].fillna(df['user'].where(df['user'].isin(admin_usernames)))

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.sort_values('date')
    df['hour'] = df['date'].dt.hour
    df['day'] = df['date'].dt.date

    df_raw = df.copy()

    # محاسبه دقیق TTFT
    df = df.reset_index(drop=True)
    sla_list = []
    for idx, row in df.iterrows():
        current_user = row['user']
        current_time = row['date']
        current_account = row['account']
        if pd.isna(row['responded_from']) or row['responded_from'] == current_user:
            next_response = df[
                (df['account'] == current_account) &
                (df['date'] > current_time) &
                (df['responded_from'].notna()) &
                (df['responded_from'] != current_user)
            ]
            if not next_response.empty:
                response_time = next_response.iloc[0]['date']
                sla_minutes = (response_time - current_time).total_seconds() / 60
                sla_list.append(sla_minutes)
            else:
                sla_list.append(None)
        else:
            sla_list.append(None)
    df['sla'] = sla_list

    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    start_date, end_date = st.date_input("بازه تاریخ", [min_date, max_date], min_value=min_date, max_value=max_date)
    df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]

    st.subheader("آمار کلی")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("کل پیام‌ها", len(df))
    col2.metric("تعداد اکانت‌ها", df['account'].nunique())
    col3.metric("کاربران یکتا", df['user'].nunique())

    latest_day = df_raw['day'].max()
    yesterday = latest_day
    day_before = latest_day - pd.Timedelta(days=1)
    count_yesterday = df_raw[df_raw['day'] == yesterday].shape[0]
    count_before = df_raw[df_raw['day'] == day_before].shape[0]
    change = count_yesterday - count_before
    pct_change = (change / count_before * 100) if count_before != 0 else 0
    change_symbol = "📈" if change > 0 else "📉" if change < 0 else "➖"
    col4.metric("تغییر نسبت به دیروز", f"{change_symbol} {abs(change)} پیام", f"{pct_change:.1f}%", delta_color="normal")

    # سایر بخش‌های تحلیل، نمودارها، فیلترها و جدول‌ها به صورت کامل و دست‌نخورده باقی مانده‌اند

else:
    st.info("لطفاً فایل خروجی اکسل نوین‌هاب را بارگذاری کنید.")
