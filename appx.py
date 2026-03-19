import streamlit as st
import pandas as pd
from pathlib import Path

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ModuleNotFoundError:
    px = None
    PLOTLY_AVAILABLE = False


st.set_page_config(
    page_title="EduPro Learning Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


CLUSTER_LABELS = {
    0: "Casual Learner",
    1: "Explorer",
    2: "Specialist",
    3: "Career-Focused",
}


def apply_modern_theme() -> None:
    """Inject a lightweight Power BI style theme."""
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(239, 68, 68, 0.14), transparent 28%),
                    radial-gradient(circle at top right, rgba(56, 189, 248, 0.12), transparent 24%),
                    linear-gradient(180deg, #050816 0%, #0b1020 52%, #111827 100%);
                color: #f8fafc;
                zoom: 0.9;
            }
            .block-container {
                padding-top: 0.9rem;
                padding-bottom: 1.5rem;
                max-width: 88rem;
            }
            h1, h2, h3, h4, h5, h6, p, label, div, span {
                color: #f8fafc;
            }
            [data-testid="stSidebar"] * {
                color: #f8fafc;
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #090d18 0%, #111827 100%);
                border-right: 1px solid rgba(148, 163, 184, 0.12);
            }
            .dashboard-card {
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.92) 0%, rgba(17, 24, 39, 0.92) 100%);
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 14px 34px rgba(2, 6, 23, 0.45);
                border: 1px solid rgba(148, 163, 184, 0.12);
                margin-bottom: 1rem;
            }
            .kpi-value {
                font-size: 1.45rem;
                font-weight: 700;
                color: #f8fafc;
                line-height: 1.1;
            }
            .kpi-label {
                font-size: 0.82rem;
                color: #94a3b8;
                margin-bottom: 0.35rem;
            }
            .section-title {
                font-size: 1rem;
                font-weight: 700;
                color: #f8fafc;
                margin-bottom: 0.6rem;
            }
            div[data-testid="stMetric"] {
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.9) 0%, rgba(17, 24, 39, 0.92) 100%);
                border: 1px solid rgba(148, 163, 184, 0.14);
                padding: 0.7rem 0.85rem;
                border-radius: 16px;
                box-shadow: 0 12px 32px rgba(2, 6, 23, 0.35);
            }
            div[data-testid="stAlert"] {
                color: #f8fafc;
                background: rgba(15, 23, 42, 0.78);
                border: 1px solid rgba(250, 204, 21, 0.25);
            }
            button[kind="primary"], button[kind="secondary"] {
                color: #f8fafc;
            }
            [data-testid="stTabs"] button {
                color: #cbd5e1;
            }
            [data-testid="stTabs"] button[aria-selected="true"] {
                color: #f87171;
            }
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div,
            div[data-baseweb="popover"] {
                background-color: #0f172a;
                color: #f8fafc;
            }
            .stSelectbox label, .stMultiSelect label {
                color: #e2e8f0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_data():
    """Load source files, clean nulls, and align profile + transaction data."""
    transaction_candidates = [
        "Final data.csv",
        "Final_data.csv",
        "Final_dataset.csv",
        "Final dataset.csv",
    ]
    profile_candidates = [
        "Learner profile.csv",
        "Learner_Profile.csv",
        "Learner profile .csv",
        "Learner Profile.csv",
    ]

    transaction_file = next((name for name in transaction_candidates if Path(name).exists()), None)
    profile_file = next((name for name in profile_candidates if Path(name).exists()), None)

    if not transaction_file or not profile_file:
        missing = []
        if not transaction_file:
            missing.append("transaction dataset")
        if not profile_file:
            missing.append("learner profile dataset")
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

    transactions = pd.read_csv(transaction_file)
    profiles = pd.read_csv(profile_file)

    for frame in (transactions, profiles):
        object_cols = frame.select_dtypes(include="object").columns
        numeric_cols = frame.select_dtypes(exclude="object").columns
        frame[object_cols] = frame[object_cols].fillna("Unknown")
        frame[numeric_cols] = frame[numeric_cols].fillna(0)

    if "Cluster" not in transactions.columns and "UserID" in transactions.columns:
        transactions = transactions.merge(
            profiles[["UserID", "Cluster"]].drop_duplicates(),
            on="UserID",
            how="left",
        )

    if "Amount" not in transactions.columns and "CoursePrice" in transactions.columns:
        transactions["Amount"] = transactions["CoursePrice"]

    transactions["Cluster"] = pd.to_numeric(transactions["Cluster"], errors="coerce").fillna(-1).astype(int)
    profiles["Cluster"] = pd.to_numeric(profiles["Cluster"], errors="coerce").fillna(-1).astype(int)

    return transactions, profiles


def initialize_state(default_categories, default_levels):
    """Set app-level state once so widgets can stay synchronized."""
    defaults = {
        "selected_cluster": "All",
        "selected_user": "All Users",
        "selected_categories": default_categories,
        "selected_levels": default_levels,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_user_options(data: pd.DataFrame, cluster_value, categories, levels):
    """Return user options based on current non-user filters."""
    working = data.copy()

    if cluster_value != "All":
        working = working[working["Cluster"] == int(cluster_value)]
    if categories:
        working = working[working["CourseCategory"].isin(categories)]
    if levels:
        working = working[working["CourseLevel"].isin(levels)]

    users = sorted(working["UserID"].dropna().astype(str).unique().tolist())
    return ["All Users"] + users


def filter_data(
    transactions: pd.DataFrame,
    profiles: pd.DataFrame,
    cluster_value,
    categories,
    levels,
    user_id,
):
    """Apply the shared global filters consistently across tables and visuals."""
    filtered_tx = transactions.copy()
    filtered_profiles = profiles.copy()

    if cluster_value != "All":
        cluster_value = int(cluster_value)
        filtered_tx = filtered_tx[filtered_tx["Cluster"] == cluster_value]
        filtered_profiles = filtered_profiles[filtered_profiles["Cluster"] == cluster_value]

    if categories:
        filtered_tx = filtered_tx[filtered_tx["CourseCategory"].isin(categories)]

    if levels:
        filtered_tx = filtered_tx[filtered_tx["CourseLevel"].isin(levels)]

    users_after_course_filters = filtered_tx["UserID"].dropna().astype(str).unique().tolist()
    if categories or levels:
        filtered_profiles = filtered_profiles[
            filtered_profiles["UserID"].astype(str).isin(users_after_course_filters)
        ]

    if user_id != "All Users":
        filtered_tx = filtered_tx[filtered_tx["UserID"].astype(str) == str(user_id)]
        filtered_profiles = filtered_profiles[filtered_profiles["UserID"].astype(str) == str(user_id)]

    return filtered_tx, filtered_profiles


def sync_cluster_from_profile():
    """Allow the profile tab radio to drive the global cluster filter."""
    st.session_state["selected_cluster"] = st.session_state["profile_cluster"]


def sync_user_from_profile():
    """Allow the profile tab user selector to drive the global user filter."""
    st.session_state["selected_user"] = st.session_state["profile_user"]


def get_active_user(user_options):
    """Resolve the profile/recommendation user safely from current filters."""
    selected_user = st.session_state["selected_user"]
    valid_users = [user for user in user_options if user != "All Users"]

    if selected_user != "All Users" and selected_user in valid_users:
        return selected_user
    if valid_users:
        return valid_users[0]
    return None


def build_recommendations(
    transactions: pd.DataFrame,
    profiles: pd.DataFrame,
    user_id,
    categories,
    levels,
):
    """Recommend popular courses inside the user's cluster that they have not taken yet."""
    if not user_id:
        return pd.DataFrame(columns=["CourseName", "CourseCategory", "CourseLevel", "Enrollments"])

    profile_match = profiles[profiles["UserID"].astype(str) == str(user_id)]
    if profile_match.empty:
        return pd.DataFrame(columns=["CourseName", "CourseCategory", "CourseLevel", "Enrollments"])

    user_cluster = int(profile_match["Cluster"].iloc[0])
    cluster_transactions = transactions[transactions["Cluster"] == user_cluster].copy()

    if categories:
        cluster_transactions = cluster_transactions[cluster_transactions["CourseCategory"].isin(categories)]
    if levels:
        cluster_transactions = cluster_transactions[cluster_transactions["CourseLevel"].isin(levels)]

    taken_courses = set(
        transactions[transactions["UserID"].astype(str) == str(user_id)]["CourseName"].dropna().tolist()
    )

    recommendations = (
        cluster_transactions.groupby(["CourseName", "CourseCategory", "CourseLevel"])
        .size()
        .reset_index(name="Enrollments")
    )

    recommendations = recommendations[~recommendations["CourseName"].isin(taken_courses)]
    recommendations = recommendations.sort_values(
        ["Enrollments", "CourseName"], ascending=[False, True]
    ).reset_index(drop=True)

    return recommendations


def metric_card(title: str, value: str):
    """Render a custom KPI card."""
    st.markdown(
        f"""
        <div class="dashboard-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bar_chart(data, x, y, title, color=None, horizontal=False):
    """Render Plotly when available, otherwise fall back to Streamlit charts."""
    if data.empty:
        st.info(f"No data available for {title.lower()}.")
        return

    if PLOTLY_AVAILABLE:
        figure = px.bar(
            data,
            x=(y if horizontal else x),
            y=(x if horizontal else y),
            color=color,
            orientation="h" if horizontal else "v",
            title=title,
            template="plotly_white",
            text=y if horizontal else None,
        )
        if horizontal:
            figure.update_layout(yaxis={"categoryorder": "total ascending"})
        if color is None:
            figure.update_layout(showlegend=False)
        st.plotly_chart(figure, use_container_width=True)
        return

    fallback = data.copy()
    if color and color in fallback.columns:
        fallback = fallback.groupby(x, as_index=False)[y].sum(numeric_only=True)
    st.subheader(title)
    st.bar_chart(fallback.set_index(x)[y])


def render_pie_chart(data, names, values, title):
    """Render a pie chart with Plotly or a bar fallback."""
    if data.empty:
        st.info(f"No data available for {title.lower()}.")
        return

    if PLOTLY_AVAILABLE:
        figure = px.pie(
            data,
            names=names,
            values=values,
            hole=0.45,
            title=title,
            template="plotly_white",
        )
        figure.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(figure, use_container_width=True)
        return

    st.subheader(title)
    st.bar_chart(data.set_index(names)[values])


def render_histogram(data, x, title, color=None, nbins=25):
    """Render a histogram with Plotly or a simple fallback."""
    if data.empty:
        st.info(f"No data available for {title.lower()}.")
        return

    if PLOTLY_AVAILABLE:
        figure = px.histogram(
            data,
            x=x,
            color=color,
            nbins=nbins,
            title=title,
            template="plotly_white",
        )
        figure.update_layout(bargap=0.08)
        st.plotly_chart(figure, use_container_width=True)
        return

    st.subheader(title)
    st.bar_chart(data[[x]])


def main():
    apply_modern_theme()

    transactions, profiles = load_data()

    categories = sorted(transactions["CourseCategory"].dropna().astype(str).unique().tolist())
    levels = sorted(transactions["CourseLevel"].dropna().astype(str).unique().tolist())
    initialize_state(categories, levels)

    user_options = get_user_options(
        transactions,
        st.session_state["selected_cluster"],
        st.session_state["selected_categories"],
        st.session_state["selected_levels"],
    )

    if st.session_state["selected_user"] not in user_options:
        st.session_state["selected_user"] = "All Users"

    st.title("EduPro Learning Intelligence Dashboard")
    st.caption("Learner profile explorer, cluster visualization, personalized recommendations, and segment comparison.")

    if not PLOTLY_AVAILABLE:
        st.warning("`plotly` is not installed. The app is using Streamlit chart fallbacks. Install `plotly` for full interactivity.")

    with st.sidebar:
        st.header("Global Filters")

        cluster_options = ["All", 0, 1, 2, 3]
        st.session_state["selected_cluster"] = st.selectbox(
            "Cluster",
            options=cluster_options,
            index=cluster_options.index(st.session_state["selected_cluster"]),
        )

        st.session_state["selected_categories"] = st.multiselect(
            "Course Category",
            options=categories,
            default=st.session_state["selected_categories"],
        )

        st.session_state["selected_levels"] = st.multiselect(
            "Course Level",
            options=levels,
            default=st.session_state["selected_levels"],
        )

        refreshed_user_options = get_user_options(
            transactions,
            st.session_state["selected_cluster"],
            st.session_state["selected_categories"],
            st.session_state["selected_levels"],
        )
        if st.session_state["selected_user"] not in refreshed_user_options:
            st.session_state["selected_user"] = "All Users"

        st.session_state["selected_user"] = st.selectbox(
            "User",
            options=refreshed_user_options,
            index=refreshed_user_options.index(st.session_state["selected_user"]),
        )

    base_tx, base_profiles = filter_data(
        transactions,
        profiles,
        st.session_state["selected_cluster"],
        st.session_state["selected_categories"],
        st.session_state["selected_levels"],
        "All Users",
    )
    filtered_tx, filtered_profiles = filter_data(
        transactions,
        profiles,
        st.session_state["selected_cluster"],
        st.session_state["selected_categories"],
        st.session_state["selected_levels"],
        st.session_state["selected_user"],
    )

    current_user_options = get_user_options(
        transactions,
        st.session_state["selected_cluster"],
        st.session_state["selected_categories"],
        st.session_state["selected_levels"],
    )
    active_user = get_active_user(current_user_options)

    profile_user_options = [user for user in current_user_options if user != "All Users"]
    if profile_user_options:
        desired_profile_user = active_user if active_user in profile_user_options else profile_user_options[0]
        if st.session_state.get("profile_user") not in profile_user_options:
            st.session_state["profile_user"] = desired_profile_user

    profile_row = pd.DataFrame()
    if active_user:
        profile_row = profiles[profiles["UserID"].astype(str) == str(active_user)].head(1)

    tab_profile, tab_clusters, tab_reco, tab_segments = st.tabs(
        ["Profile Explorer", "Cluster Dashboard", "Recommendations", "Segment Comparison"]
    )

    with tab_profile:
        st.markdown('<div class="section-title">Learner Profile Explorer</div>', unsafe_allow_html=True)

        col_a, col_b = st.columns([1.1, 1.2])
        with col_a:
            st.radio(
                "Cluster Selection",
                options=["All", 0, 1, 2, 3],
                key="profile_cluster",
                index=["All", 0, 1, 2, 3].index(st.session_state["selected_cluster"]),
                horizontal=True,
                on_change=sync_cluster_from_profile,
            )
        with col_b:
            profile_default = active_user if active_user in profile_user_options else (
                profile_user_options[0] if profile_user_options else None
            )
            st.selectbox(
                "Profile User",
                options=profile_user_options if profile_user_options else ["No matching users"],
                index=(profile_user_options.index(profile_default) if profile_default else 0),
                key="profile_user",
                disabled=not profile_user_options,
                on_change=sync_user_from_profile,
            )

        if profile_row.empty:
            st.info("No learner profile matches the current filters.")
        else:
            learner = profile_row.iloc[0]
            kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
            with kpi_1:
                metric_card("Age", f"{int(learner.get('UserAge', 0))}")
            with kpi_2:
                metric_card("Courses", f"{int(learner.get('TotalCourses', 0))}")
            with kpi_3:
                metric_card("Spend", f"${float(learner.get('AvgSpend', 0)):.2f}")
            with kpi_4:
                metric_card("Diversity", f"{int(learner.get('DiversityScore', 0))}")

            cluster_name = CLUSTER_LABELS.get(int(learner.get("Cluster", -1)), "Unassigned")
            st.success(f"Cluster {int(learner.get('Cluster', -1))}: {cluster_name}")

            extra_1, extra_2, extra_3 = st.columns(3)
            extra_1.metric("Average Rating", f"{float(learner.get('AvgRating', 0)):.2f}")
            extra_2.metric("Advanced Courses", f"{int(learner.get('AdvancedCourses', 0))}")
            extra_3.metric("Average Duration", f"{float(learner.get('AvgDuration', 0)):.2f}")

    with tab_clusters:
        st.markdown('<div class="section-title">Cluster Visualization Dashboard</div>', unsafe_allow_html=True)

        if base_tx.empty or base_profiles.empty:
            st.info("No cluster data matches the current filters.")
        else:
            cluster_mix = (
                base_profiles.groupby("Cluster")
                .size()
                .reset_index(name="Learners")
                .sort_values("Cluster")
            )
            category_mix = (
                base_tx.groupby(["Cluster", "CourseCategory"])
                .size()
                .reset_index(name="Enrollments")
            )

            col_1, col_2 = st.columns(2)

            with col_1:
                render_bar_chart(
                    cluster_mix,
                    x="Cluster",
                    y="Learners",
                    title="Learner Distribution by Cluster",
                    color="Cluster",
                )
            with col_2:
                render_bar_chart(
                    category_mix,
                    x="Cluster",
                    y="Enrollments",
                    title="Category Mix Across Clusters",
                    color="CourseCategory",
                )

            render_histogram(
                base_tx,
                x="Amount",
                color="CourseLevel",
                nbins=25,
                title="Spend Distribution by Active Filters",
            )
            analytics_col_1, analytics_col_2 = st.columns(2)
            category_counts = (
                filtered_tx.groupby("CourseCategory")
                .size()
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
            )
            level_counts = (
                filtered_tx.groupby("CourseLevel")
                .size()
                .reset_index(name="Count")
                .sort_values("Count", ascending=False)
            )

            with analytics_col_1:
                render_pie_chart(
                    category_counts,
                    names="CourseCategory",
                    values="Count",
                    title="Course Category Distribution",
                )
            with analytics_col_2:
                render_bar_chart(
                    level_counts,
                    x="CourseLevel",
                    y="Count",
                    color="CourseLevel",
                    title="Course Level Distribution",
                )

    with tab_reco:
        st.markdown('<div class="section-title">Personalized Course Recommendations</div>', unsafe_allow_html=True)
        st.caption("Recommendations use the learner's assigned cluster and remove courses already taken.")

        if not active_user:
            st.info("Recommendations appear once the current filters return at least one user.")
        else:
            if st.session_state["selected_user"] == "All Users":
                st.caption(f"Showing recommendations for {active_user} because no single global user is pinned.")

            recs = build_recommendations(
                base_tx,
                profiles,
                active_user,
                st.session_state["selected_categories"],
                st.session_state["selected_levels"],
            )

            st.dataframe(
                recs[["CourseName", "CourseCategory", "CourseLevel", "Enrollments"]].head(12),
                use_container_width=True,
                hide_index=True,
            )

            if recs.empty:
                st.warning("No new courses are available for the current combination of cluster, category, and level filters.")
            else:
                render_bar_chart(
                    recs.head(10),
                    x="CourseName",
                    y="Enrollments",
                    title="Top Recommended Courses",
                    color="CourseCategory",
                    horizontal=True,
                )

    with tab_segments:
        st.markdown('<div class="section-title">Segment Comparison Panels</div>', unsafe_allow_html=True)

        segment_source = filtered_profiles.copy()

        if segment_source.empty:
            st.info("No segment data matches the current filters.")
            return

        cluster_counts = (
            segment_source.groupby("Cluster")
            .size()
            .reset_index(name="Users")
            .sort_values("Cluster")
        )
        cluster_summary = (
            segment_source.groupby("Cluster")
            .mean(numeric_only=True)
            .reset_index()
            .sort_values("Cluster")
        )

        render_bar_chart(
            cluster_counts,
            x="Cluster",
            y="Users",
            color="Cluster",
            title="Cluster Distribution",
        )

        metric_columns = st.columns(4)
        for idx, cluster_id in enumerate([0, 1, 2, 3]):
            cluster_size = int(cluster_counts.loc[cluster_counts["Cluster"] == cluster_id, "Users"].sum())
            avg_courses = cluster_summary.loc[
                cluster_summary["Cluster"] == cluster_id, "TotalCourses"
            ].mean()
            label = CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}")
            metric_columns[idx].metric(label, f"{cluster_size} users", f"{0 if pd.isna(avg_courses) else avg_courses:.1f} avg courses")

        st.dataframe(cluster_summary, use_container_width=True, hide_index=True)

        render_bar_chart(
            cluster_summary,
            x="Cluster",
            y="TotalCourses",
            color="Cluster",
            title="Average Total Courses by Cluster",
        )


if __name__ == "__main__":
    main()
