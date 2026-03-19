import streamlit as st
import pandas as pd
import plotly.express as px


# LOAD DATA

df = pd.read_csv("Final_dataset.csv")
learner_profile = pd.read_csv("Learner_Profile.csv")

learner_profile.fillna(0, inplace=True)

st.set_page_config(layout="wide", page_title="EduPro Dashboard")

st.title("EduPro Interactive Learning Intelligence Dashboard")


# SIDEBAR FILTERS

st.sidebar.header("Filters")

cluster_filter = st.sidebar.radio(
    "Select Cluster",
    ["All"] + sorted(learner_profile['Cluster'].unique().tolist())
)

user_sidebar = st.sidebar.selectbox("Select User", learner_profile['UserID'])

level_filter = st.sidebar.multiselect(
    "Course Level",
    df['CourseLevel'].unique(),
    default=list(df['CourseLevel'].unique())
)

category_filter = st.sidebar.multiselect(
    "Course Category",
    df['CourseCategory'].unique(),
    default=list(df['CourseCategory'].unique())
)


# APPLY CLUSTER FILTER

if cluster_filter != "All":
    filtered_users = learner_profile[
        learner_profile['Cluster'] == cluster_filter
    ]['UserID']
    df_filtered = df[df['UserID'].isin(filtered_users)]
else:
    df_filtered = df.copy()


# TABS

tab1, tab2, tab3, tab4 = st.tabs([
    "Profile",
    "Recommendations",
    "Analytics",
    "Segments"
])

# -----------------------------
# TAB 1: PROFILE (CLICKABLE CLUSTERS)
# -----------------------------
with tab1:
    st.subheader("Learner Profile")

    st.markdown("### Select Cluster")

    cluster_buttons = st.radio(
        "Choose Cluster",
        options=["All", 0, 1, 2, 3],
        horizontal=True
    )

    # Filter users based on selected cluster
    if cluster_buttons != "All":
        users_in_cluster = learner_profile[
            learner_profile['Cluster'] == cluster_buttons
        ]['UserID']
    else:
        users_in_cluster = learner_profile['UserID']

    user_selected = st.selectbox("Select User", users_in_cluster)

    profile = learner_profile[
        learner_profile['UserID'] == user_selected
    ].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Age", int(profile['UserAge']))
    col2.metric("Courses", int(profile['TotalCourses']))
    col3.metric("Avg Spend", round(float(profile['AvgSpend']), 2))
    col4.metric("Diversity", int(profile['DiversityScore']))

    col5, col6 = st.columns(2)

    col5.metric("Avg Rating", round(float(profile['AvgRating']), 2))
    col6.metric("Advanced Courses", int(profile['AdvancedCourses']))

    cluster = int(profile['Cluster'])

    cluster_names = {
        0: "Casual Learner",
        1: "Explorer",
        2: "Specialist",
        3: "Career-Focused"
    }

    st.success(f"Cluster {cluster}: {cluster_names.get(cluster)}")

# -----------------------------
# RECOMMENDATION FUNCTION
# -----------------------------
def recommend(user_id):
    taken = df_filtered[df_filtered['UserID'] == user_id]['CourseName'].tolist()

    cluster_data = df_filtered.merge(
        learner_profile[['UserID', 'Cluster']],
        on='UserID'
    )

    popular = (
        cluster_data.groupby(['Cluster', 'CourseName'])
        .size()
        .reset_index(name='Enrollments')
    )

    cluster = learner_profile.loc[
        learner_profile['UserID'] == user_id, 'Cluster'
    ].values[0]

    rec = popular[popular['Cluster'] == cluster]

    rec_df = rec.merge(
        df_filtered[['CourseName','CourseCategory','CourseLevel']].drop_duplicates(),
        on='CourseName'
    )

    rec_df = rec_df[~rec_df['CourseName'].isin(taken)]

    return rec_df.sort_values('Enrollments', ascending=False)

# -----------------------------
# TAB 2: RECOMMENDATIONS
# -----------------------------
with tab2:
    st.subheader(" Personalized Recommendations")

    rec_df = recommend(user_sidebar)

    rec_df = rec_df[
        (rec_df['CourseLevel'].isin(level_filter)) &
        (rec_df['CourseCategory'].isin(category_filter))
    ]

    st.dataframe(rec_df[['CourseName','CourseCategory','CourseLevel']].head(10))

    if not rec_df.empty:
        fig = px.bar(
            rec_df.head(10),
            x="CourseName",
            color="CourseCategory",
            title="Top Recommended Courses"
        )
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# TAB 3: ANALYTICS
# -----------------------------
with tab3:
    st.subheader("Platform Analytics")

    col1, col2 = st.columns(2)

    cat_counts = df_filtered['CourseCategory'].value_counts()

    fig1 = px.pie(
        values=cat_counts.values,
        names=cat_counts.index,
        title="Course Category Distribution"
    )

    col1.plotly_chart(fig1, use_container_width=True)

    level_counts = df_filtered['CourseLevel'].value_counts()

    fig2 = px.bar(
        x=level_counts.index,
        y=level_counts.values,
        title="Course Level Distribution"
    )

    col2.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# TAB 4: SEGMENTS
# -----------------------------
with tab4:
    st.subheader("Segment Analysis")

    cluster_counts = learner_profile['Cluster'].value_counts()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Cluster 0", cluster_counts.get(0, 0))
    c2.metric("Cluster 1", cluster_counts.get(1, 0))
    c3.metric("Cluster 2", cluster_counts.get(2, 0))
    c4.metric("Cluster 3", cluster_counts.get(3, 0))

    fig3 = px.bar(
        x=cluster_counts.index,
        y=cluster_counts.values,
        title="Cluster Distribution"
    )

    st.plotly_chart(fig3, use_container_width=True)

    segment_stats = learner_profile.groupby('Cluster').mean(numeric_only=True)

    st.dataframe(segment_stats)

    fig_compare = px.bar(
        learner_profile,
        x="Cluster",
        y="TotalCourses",
        color="Cluster",
        title="Courses by Cluster"
    )

    st.plotly_chart(fig_compare, use_container_width=True)