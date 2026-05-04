# Product Management: Bridging Vision and Engineering

This document explains how Product Management (PM) turns a "cool idea" into a working, scalable data platform. For those new to the field, PM is the bridge between **Business Goals** (What we want to achieve) and **Technical Implementation** (How we build it).

## 1. The PRD: Our "North Star"
Every project starts with a **Product Requirements Document (PRD)**. In this repository, that is our `.agents/rules/00-product-vision.md`.
*   **The Concept**: It defines the "What" and the "Why" before we write a single line of code. It ensures everyone—from the Data Engineer to the Stakeholder—is on the same page.
*   **Project Example**: Our PRD clearly defines that we are tracking 4 specific channels under the Fókusz Stúdió hierarchy. This prevents "Scope Creep"—the tendency for projects to get bigger and messier than originally planned.

## 2. Phased Onboarding & The MVP
We don't try to build the whole world at once. We use the concept of a **Minimum Viable Product (MVP)**.
*   **The Concept**: Build the smallest version of the product that is still useful, then iterate.
*   **Phase 1 (Fókusz Stúdió)**: This is our MVP. By starting with 4 channels under 1 studio, we can perfect the data model and the dbt transformation logic on a small, manageable scale.
*   **The Strategy**: Once the "Template" is solid, **Phase 2** (Cérnagyár expansion) becomes a repetitive scaling task rather than a risky re-engineering effort.

## 3. Metadata Hierarchy: Translating Data to Reality
Data in its raw form is just numbers and IDs. PMs ensure those numbers make sense to the people using them.
*   **The Structure**: `Organization > Studio/Creator > Channel`.
*   **The Value**: A creator doesn't want to see "ID: UC...". They want to see "Fókusz Csoport" performance. By building a **Master Data** table, we bridge the gap between "Technical API IDs" and "Business Reality." This allows for "Roll-up" reporting (e.g., seeing total views for the whole Cérnagyár organization).

## 4. Environment Strategy: Managing Risk
Why do we bother with **DEV** and **PROD** environments in a hobby project?
*   **The Concept**: Risk Mitigation and Uptime.
*   **Project Example**: We build and test new dbt models or Snowpark scripts in the **DEV** environment. Only when we are 100% sure the data is accurate do we deploy it to **PROD**. This ensures that the Streamlit app—the actual "Product"—never shows broken charts or incorrect metrics.

## 5. Cost Governance: The ROI of a Hobby
In PM, we always look at the **Return on Investment (ROI)**. We want the most value for the least cost.
*   **The Problem**: Snowflake is powerful but can be expensive if left unmonitored.
*   **The Solution**: We use **Resource Monitors** and **X-Small warehouses** with aggressive auto-suspend.
*   **Business Impact**: This ensures the project remains a "Hobby" cost-wise (~EUR 5/month) while providing "Enterprise" level insights.

## 6. Metric Prioritization: Signal vs. Noise
More data isn't always better. PMs decide which metrics actually drive decisions.
*   **The Concept**: Metric Prioritization (Focusing on the "Signal").
*   **Project Example**: We focus on **Subscribers, Views, Likes, and Comments**. While the YouTube API provides hundreds of fields, these four give the most immediate health check of a channel's growth and audience engagement.

---
*Created by **Technical Product Manager** — Visionary & Strategist*

