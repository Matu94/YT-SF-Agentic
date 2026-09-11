# Product Management: Bridging Vision and Engineering

This document explains how Product Management (PM) turns a "cool idea" into a working, scalable data platform. For those new to the field, PM is the bridge between **Business Goals** (What we want to achieve) and **Technical Implementation** (How we build it).

## 1. The PRD: Our "North Star"
Every project starts with a **Product Requirements Document (PRD)**. In this repository, that is our `.agents/rules/00-product-vision.md`.
*   **The Concept**: It defines the "What" and the "Why" before we write a single line of code. It ensures everyone—from the Data Engineer to the Stakeholder—is on the same page.
*   **Project Example**: Our PRD clearly defines that we are continuously tracking a growing list of Hungarian YouTube channels. This prevents "Scope Creep"—the tendency for projects to get bigger and messier than originally planned.

## 2. Continuous Delivery & Expansion
We iterate constantly by using a **Continuous Delivery** approach.
*   **The Concept**: Deliver small, incremental updates to production frequently.
*   **The Strategy**: Once a feature or data model is solid, it gets pushed to PROD immediately. We scale seamlessly as we add more channels, relying on robust automation rather than phased releases.

## 3. Metadata Hierarchy: Translating Data to Reality
Data in its raw form is just numbers and IDs. PMs ensure those numbers make sense to the people using them.
*   **The Structure**: `Organization > Studio/Creator > Channel`.
*   **The Value**: A creator doesn't want to see "ID: UC...". They want to see their channel's name in the performance reports. By building a **Master Data** table, we bridge the gap between "Technical API IDs" and "Business Reality." This allows for "Roll-up" reporting across broader networks or organizations.

## 4. Environment Strategy: Managing Risk
Why do we bother with **DEV** and **PROD** environments in a hobby project?
*   **The Concept**: Risk Mitigation and Uptime.
*   **Project Example**: We build and test new dbt models or Snowpark scripts in the **DEV** environment. Only when we are 100% sure the data is accurate do we deploy it to **PROD**. This ensures that the Streamlit app—the actual "Product"—never shows broken charts or incorrect metrics.

## 5. Cost Governance: The ROI of a Hobby
In PM, we always look at the **Return on Investment (ROI)**. We want the most value for the least cost.
*   **The Problem**: Snowflake is powerful but can be expensive if left unmonitored.
*   **The Solution**: We use **Resource Monitors** and **X-Small warehouses** with aggressive auto-suspend.
*   **Business Impact**: This ensures the project remains highly cost-effective (~EUR 40/month total across all 4 dedicated compute workloads) while providing "Enterprise" level insights as the project grows.

## 6. Metric Prioritization: Signal vs. Noise
More data isn't always better. PMs decide which metrics actually drive decisions.
*   **The Concept**: Metric Prioritization (Focusing on the "Signal").
*   **Project Example**: We focus on **Subscribers, Views, Likes, and Comments**. While the YouTube API provides hundreds of fields, these four give the most immediate health check of a channel's growth and audience engagement.

---
*Created by **Technical Product Manager** — Visionary & Strategist*

