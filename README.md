# Student Segmentation and Personalized Course Recommendation System for EduPro

## Internship Project  
**Organization:** Unified Mentor 
**Domain:** Data Science 
**Project Type:** End-to-End ML + Dashboard System  

---

## Project Overview

This project focuses on building a **student-centric personalization system** for the EduPro platform.

Traditional recommendation systems follow a **one-size-fits-all approach**, which fails to address the diverse needs of learners. This project introduces a **data-driven solution** that segments users based on behavior and provides **personalized course recommendations**.

---

## Problem Statement

EduPro currently faces:

- Generic course recommendations  
- Limited understanding of learner behavior  
- No structured segmentation  

### Impact:
- Poor content discovery  
- Low engagement  
- Reduced retention  

 Solution: Build a **segmentation + recommendation engine**

---

## Background & Context

Online learners are diverse:

- Explorers → try multiple domains  
- Specialists → focus on one domain  
- Career-oriented → pursue certifications  

Generic recommendations fail to:
- Maximize engagement  
- Improve completion rates  
- Build long-term loyalty  

---

## Dataset Description

The dataset consists of multiple sheets:

### Users
- UserID  
- Age  
- Gender  

### Courses
- CourseID  
- CourseCategory  
- CourseType  
- CourseLevel  
- CourseRating  

### Transactions
- UserID  
- CourseID  
- TransactionDate  
- Amount  

---

## Feature Engineering

Learner-level features were engineered to capture behavior:

### Engagement Features
- TotalCourses  
- Enrollment frequency  
- Courses per category  

### Preference Features
- Preferred category  
- Preferred level  
- Avg course rating  

### Behavioral Features
- Avg spending  
- Diversity score  
- Learning depth index  

---

## Methodology

### Data Aggregation
- Combined all datasets  
- Created learner profiles  

### Data Preprocessing
- Scaling (StandardScaler)  
- Encoding categorical variables  
- Handling missing values  

### Learner Segmentation

Used **Unsupervised Learning**:

- K-Means Clustering  
- Elbow Method  
- Silhouette Score  

---

## Learner Segments Identified

| Cluster | Type |
|--------|------|
| 0 | Casual Learners |
| 1 | Explorers |
| 2 | Specialists |
| 3 | Career-Focused Users |

---

## Recommendation System

A **Hybrid Recommendation Model** was implemented:

-  Cluster-based filtering  
-  Content-based recommendations  
-  Popular courses within cluster  
-  Rating-weighted ranking  
-  Removal of already enrolled courses  

---

## Dashboard (Streamlit)

An interactive web application was developed with:

### Core Modules
- Learner Profile Explorer  
- Cluster Visualization Dashboard  
- Personalized Recommendations  
- Segment Comparison  

### User Capabilities
- Select learner  
- View assigned segment  
- Get recommended courses  
- Filter by category & level  

### Advanced Features
-  Power BI-style cluster filtering  
-  Interactive charts (Plotly)  
-  Dynamic filters  
-  Tab-based navigation  

---

##  Key Insights

- AI & Data Science dominate course demand  
- Beginner-level courses attract most users  
- Revenue follows Pareto principle (few users generate most revenue)  
- Strong need for personalization  
- Learner behavior is multi-dimensional  

---

##  Evaluation Metrics

| Metric | Purpose |
|------|--------|
| Silhouette Score | Cluster quality |
| Intra-Cluster Similarity | Behavioral consistency |
| Recommendation Precision | Relevance |
| Engagement Lift | Performance impact |

---

## Deployment

The system is deployed using **Streamlit Cloud**.

 Live App: https://student-segmentation-edupro.onrender.com/

---

## How to Run

```bash
pip install -r requirements.txt
python -m streamlit run app.py
