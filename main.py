# -*- coding: utf-8 -*-
"""
서울 기온 순위 분석기
- seoul.csv (1907~ 서울 기상관측 데이터)
- 두 날짜를 선택하면 해당 기간의 평균기온이 역대 같은 기간 중 몇 위인지 보여줍니다.
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime

# ──────────────────────────────────────────────
# 페이지 기본 설정
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="서울 기온 순위 분석기",
    page_icon="🌡️",
    layout="wide",
)

# ──────────────────────────────────────────────
# 스타일 (CSS)
# ──────────────────────────────────────────────
st.markdown("""
<style>
/* 전체 배경 */
.stApp {
    background: linear-gradient(160deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
}
/* 제목 */
.big-title {
    font-size: 42px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -1px;
    margin-bottom: 0px;
}
.sub-title {
    font-size: 16px;
    color: #9fd3e8;
    margin-top: 4px;
    margin-bottom: 24px;
}
/* 순위 카드 */
.rank-card {
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 22px;
    padding: 28px 24px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    height: 100%;
}
.rank-label {
    font-size: 14px;
    color: #a8c6d8;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.rank-value {
    font-size: 46px;
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
}
.rank-unit {
    font-size: 15px;
    color: #cfe6f2;
    margin-top: 6px;
}
/* 하이라이트 박스 */
.hero-box {
    background: linear-gradient(135deg, rgba(255,255,255,0.14), rgba(255,255,255,0.05));
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 26px;
    padding: 34px 30px;
    text-align: center;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}
.hero-main {
    font-size: 68px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1;
    margin: 8px 0;
}
.hero-sub {
    font-size: 18px;
    color: #d8ecf7;
}
.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 700;
    margin-top: 12px;
}
/* 사이드바 */
section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.35);
}
/* 일반 텍스트 흰색 */
.stMarkdown, label, p { color: #eaf4fa !important; }
h2, h3, h4 { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# 데이터 로드
# ──────────────────────────────────────────────
@st.cache_data
def load_data(path="seoul.csv"):
    df = pd.read_csv(path, encoding="utf-8-sig")

    # 컬럼명 앞뒤 공백 제거
    df.columns = [c.strip() for c in df.columns]

    # 날짜 컬럼: 앞에 탭/공백이 붙어 있으므로 제거
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 숫자 변환
    for col in ["평균기온", "최저기온", "최고기온"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 날짜가 없거나 기온이 전부 없는 행 제거
    df = df.dropna(subset=["날짜"])
    df = df.dropna(subset=["평균기온", "최저기온", "최고기온"], how="all")

    df = df.sort_values("날짜").reset_index(drop=True)

    # 파생 컬럼
    df["연"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일"] = df["날짜"].dt.day
    df["월일"] = df["날짜"].dt.strftime("%m-%d")
    df["연중일"] = df["날짜"].dt.dayofyear

    return df


try:
    df = load_data("seoul.csv")
except FileNotFoundError:
    st.error("❌ 'seoul.csv' 파일을 찾을 수 없습니다. app.py와 같은 폴더에 넣어주세요.")
    st.stop()


MIN_DATE = df["날짜"].min().date()
MAX_DATE = df["날짜"].max().date()


# ──────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────
st.markdown('<div class="big-title">🌡️ 서울 기온 순위 분석기</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-title">📅 관측 기간 &nbsp;|&nbsp; <b>{MIN_DATE}</b> ~ <b>{MAX_DATE}</b>'
    f' &nbsp;&nbsp;·&nbsp;&nbsp; 총 <b>{len(df):,}</b>일의 기록</div>',
    unsafe_allow_html=True
)


# ──────────────────────────────────────────────
# 사이드바 - 입력
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔎 기간 선택")

    default_end = MAX_DATE
    default_start = default_end - datetime.timedelta(days=6)
    if default_start < MIN_DATE:
        default_start = MIN_DATE

    picked = st.date_input(
        "분석할 기간 (시작일 ~ 종료일)",
        value=(default_start, default_end),
        min_value=MIN_DATE,
        max_value=MAX_DATE,
        format="YYYY-MM-DD",
    )

    # 날짜 두 개가 모두 선택될 때까지 대기
    if isinstance(picked, (tuple, list)):
        if len(picked) == 2:
            start_date, end_date = picked
        else:
            st.info("👉 종료일도 선택해 주세요.")
            st.stop()
    else:
        st.info("👉 종료일도 선택해 주세요.")
        st.stop()

    st.markdown("---")
    st.markdown("## ⚙️ 분석 옵션")

    target_col = st.radio(
        "기준 기온",
        ["평균기온", "최고기온", "최저기온"],
        index=0,
    )

    order = st.radio(
        "순위 기준",
        ["더울수록 1위 (높은 순)", "추울수록 1위 (낮은 순)"],
        index=0,
    )
    descending = order.startswith("더울")

    min_coverage = st.slider(
        "비교 대상 연도의 최소 자료 비율 (%)",
        50, 100, 80, step=5,
        help="해당 기간에 결측이 많은 연도는 비교에서 제외합니다."
    )

    st.markdown("---")
    st.caption("💡 같은 '월-일' 구간을 연도별로 비교합니다.\n(예: 8/1~8/24 → 모든 해의 8/1~8/24)")


# ──────────────────────────────────────────────
# 계산 로직
# ──────────────────────────────────────────────
n_days = (end_date - start_date).days + 1
if n_days <= 0:
    st.error("종료일이 시작일보다 빨라야 합니다. 다시 선택해 주세요.")
    st.stop()
if n_days > 366:
    st.error(f"선택 기간이 {n_days}일입니다. 366일 이내로 선택해 주세요.")
    st.stop()

# 연도를 넘어가는 구간인지 판정 (예: 12/20 ~ 1/10)
cross_year = (start_date.month, start_date.day) > (end_date.month, end_date.day)


@st.cache_data
def build_yearly_stats(df, s_month, s_day, e_month, e_day, cross_year, n_days, col):
    """모든 연도에 대해 같은 월-일 구간의 통계를 계산"""
    rows = []
    years = range(int(df["연"].min()), int(df["연"].max()) + 1)

    for y in years:
        try:
            s = datetime.date(y, s_month, s_day)
        except ValueError:      # 2/29 등
            continue
        try:
            e_year = y + 1 if cross_year else y
            e = datetime.date(e_year, e_month, e_day)
        except ValueError:
            continue

        mask = (df["날짜"].dt.date >= s) & (df["날짜"].dt.date <= e)
        sub = df.loc[mask, col].dropna()

        total_days = (e - s).days + 1
        if len(sub) == 0:
            continue

        rows.append({
            "연도": y,
            "시작": s,
            "종료": e,
            "값": float(sub.mean()),
            "최댓값": float(sub.max()),
            "최솟값": float(sub.min()),
            "관측일수": int(len(sub)),
            "기간일수": int(total_days),
            "자료비율": len(sub) / total_days * 100,
        })

    return pd.DataFrame(rows)


stats = build_yearly_stats(
    df,
    start_date.month, start_date.day,
    end_date.month, end_date.day,
    cross_year, n_days, target_col
)

if stats.empty:
    st.warning("해당 구간에 대한 데이터가 없습니다.")
    st.stop()

# 자료 비율 필터
valid = stats[stats["자료비율"] >= min_coverage].copy()
if valid.empty:
    st.warning("조건을 만족하는 연도가 없습니다. 최소 자료 비율을 낮춰보세요.")
    st.stop()

# 순위 부여
valid["순위"] = valid["값"].rank(ascending=not descending, method="min").astype(int)
valid = valid.sort_values("순위").reset_index(drop=True)

total_years = len(valid)

# 선택한 연도의 결과
sel_year = start_date.year
sel_row = valid[valid["연도"] == sel_year]

if sel_row.empty:
    st.warning(
        f"선택하신 {sel_year}년 {start_date.month}/{start_date.day}~"
        f"{end_date.month}/{end_date.day} 구간은 자료가 부족해 순위 계산에서 제외되었습니다."
    )
    st.stop()

sel_row = sel_row.iloc[0]
my_rank = int(sel_row["순위"])
my_value = float(sel_row["값"])
percentile = (1 - (my_rank - 1) / total_years) * 100


# ──────────────────────────────────────────────
# 순위별 색상 / 메시지
# ──────────────────────────────────────────────
def rank_style(rank, total, descending):
    top_ratio = rank / total
    if rank == 1:
        return "#FFD700", "🥇", "역대 1위!"
    elif rank == 2:
        return "#C0C0C0", "🥈", "역대 2위!"
    elif rank == 3:
        return "#CD7F32", "🥉", "역대 3위!"
    elif rank <= 10:
        return "#FF6B6B", "🔥", "역대 TOP 10"
    elif top_ratio <= 0.1:
        return "#FF8E53", "⚡", "상위 10% 이내"
    elif top_ratio <= 0.3:
        return "#FFA94D", "📈", "상위 30% 이내"
    elif top_ratio <= 0.7:
        return "#74C0FC", "📊", "평범한 편"
    else:
        return "#4DABF7", "❄️", "하위권"


color, emoji, msg = rank_style(my_rank, total_years, descending)
direction_word = "더운" if descending else "추운"

# ──────────────────────────────────────────────
# 메인 결과 카드
# ──────────────────────────────────────────────
st.markdown("### 📌 분석 결과")

period_txt = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

st.markdown(f"""
<div class="hero-box">
    <div class="hero-sub">{period_txt} &nbsp;({n_days}일간)</div>
    <div class="hero-sub" style="opacity:.85;">{target_col} 기준 · {direction_word} 순서</div>
    <div class="hero-main" style="color:{color};">{emoji} {my_rank}<span style="font-size:30px;">위</span></div>
    <div class="hero-sub">전체 <b>{total_years}</b>개 연도 중</div>
    <div class="badge" style="background:{color}; color:#1b1b1b;">{msg} · 상위 {100-percentile:.1f}%</div>
</div>
""", unsafe_allow_html=True)

st.write("")

# ──────────────────────────────────────────────
# 지표 카드 4개
# ──────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

hottest = valid.iloc[0]
all_mean = valid["값"].mean()
diff = my_value - all_mean

cards = [
    (c1, "선택 기간 " + target_col, f"{my_value:.2f}", "℃", "#FFD43B"),
    (c2, "역대 평균", f"{all_mean:.2f}", "℃", "#74C0FC"),
    (c3, "평년 대비", f"{diff:+.2f}", "℃", "#FF8787" if diff > 0 else "#4DABF7"),
    (c4, f"1위 연도 ({int(hottest['연도'])})", f"{hottest['값']:.2f}", "℃", "#B197FC"),
]

for col_obj, label, value, unit, c in cards:
    with col_obj:
        st.markdown(f"""
        <div class="rank-card">
            <div class="rank-label">{label}</div>
            <div class="rank-value" style="color:{c};">{value}</div>
            <div class="rank-unit">{unit}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.write("")


# ──────────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 연도별 비교", "🏆 순위표", "📈 기간 내 일별 추이"])

# ── 탭1: 연도별 막대그래프 ────────────────────
with tab1:
    chart_df = valid[["연도", "값", "순위"]].copy()
    chart_df["구분"] = np.where(chart_df["연도"] == sel_year, "선택 연도", "기타")

    bar = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X("연도:O", title="연도",
                axis=alt.Axis(labelAngle=-90, labelFontSize=9, values=list(range(1900, 2031, 5)))),
        y=alt.Y("값:Q", title=f"{target_col} (℃)",
                scale=alt.Scale(zero=False)),
        color=alt.condition(
            alt.datum.연도 == sel_year,
            alt.value("#FFD43B"),
            alt.Color("값:Q", scale=alt.Scale(scheme="redyellowblue", reverse=True), legend=None)
        ),
        tooltip=[
            alt.Tooltip("연도:O", title="연도"),
            alt.Tooltip("값:Q", title=f"{target_col}", format=".2f"),
            alt.Tooltip("순위:Q", title="순위"),
        ],
    ).properties(height=420)

    mean_line = alt.Chart(pd.DataFrame({"y": [all_mean]})).mark_rule(
        color="white", strokeDash=[6, 4], size=1.5
    ).encode(y="y:Q")

    st.altair_chart((bar + mean_line).interactive(), use_container_width=True)
    st.caption("🟡 노란 막대 = 선택한 연도 &nbsp;|&nbsp; ⚪ 점선 = 역대 평균")

# ── 탭2: 순위표 ───────────────────────────────
with tab2:
    colA, colB = st.columns(2)

    with colA:
        st.markdown(f"#### 🔥 가장 {direction_word} TOP 10")
        top10 = valid.head(10)[["순위", "연도", "값", "관측일수"]].copy()
        top10["값"] = top10["값"].round(2)
        top10.columns = ["순위", "연도", f"{target_col}(℃)", "관측일수"]
        st.dataframe(top10, use_container_width=True, hide_index=True)

    with colB:
        opposite = "추운" if descending else "더운"
        st.markdown(f"#### ❄️ 가장 {opposite} TOP 10")
        bot10 = valid.tail(10).sort_values("순위", ascending=False)[
            ["순위", "연도", "값", "관측일수"]].copy()
        bot10["값"] = bot10["값"].round(2)
        bot10.columns = ["순위", "연도", f"{target_col}(℃)", "관측일수"]
        st.dataframe(bot10, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("#### 📋 전체 순위표")
    full = valid[["순위", "연도", "값", "최댓값", "최솟값", "관측일수", "자료비율"]].copy()
    full["값"] = full["값"].round(2)
    full["최댓값"] = full["최댓값"].round(1)
    full["최솟값"] = full["최솟값"].round(1)
    full["자료비율"] = full["자료비율"].round(0).astype(int).astype(str) + "%"
    full.columns = ["순위", "연도", f"평균 {target_col}(℃)", "기간 내 최고(℃)",
                    "기간 내 최저(℃)", "관측일수", "자료비율"]
    st.dataframe(full, use_container_width=True, hide_index=True, height=400)

    csv = full.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ 순위표 CSV 다운로드", csv,
                       file_name=f"seoul_rank_{start_date}_{end_date}.csv",
                       mime="text/csv")

# ── 탭3: 선택 기간 일별 추이 ──────────────────
with tab3:
    mask = (df["날짜"].dt.date >= start_date) & (df["날짜"].dt.date <= end_date)
    daily = df.loc[mask, ["날짜", "평균기온", "최저기온", "최고기온"]].copy()

    if daily.empty:
        st.info("해당 기간의 일별 데이터가 없습니다.")
    else:
        melted = daily.melt("날짜", var_name="구분", value_name="기온").dropna()

        line = alt.Chart(melted).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("날짜:T", title="날짜"),
            y=alt.Y("기온:Q", title="기온 (℃)", scale=alt.Scale(zero=False)),
            color=alt.Color("구분:N",
                            scale=alt.Scale(
                                domain=["최고기온", "평균기온", "최저기온"],
                                range=["#FF6B6B", "#FFD43B", "#4DABF7"]),
                            legend=alt.Legend(title=None, orient="top")),
            tooltip=[alt.Tooltip("날짜:T", format="%Y-%m-%d"),
                     "구분:N",
                     alt.Tooltip("기온:Q", format=".1f")],
        ).properties(height=420)

        st.altair_chart(line.interactive(), use_container_width=True)

        d1, d2, d3 = st.columns(3)
        d1.metric("기간 내 최고기온", f"{daily['최고기온'].max():.1f} ℃")
        d2.metric("기간 내 최저기온", f"{daily['최저기온'].min():.1f} ℃")
        d3.metric("기간 내 평균기온", f"{daily['평균기온'].mean():.2f} ℃")


# ──────────────────────────────────────────────
# 푸터
# ──────────────────────────────────────────────
st.markdown("---")
st.caption("데이터 출처: 기상청 기상자료개방포털 · 서울(지점번호 108) | Made with Streamlit")
