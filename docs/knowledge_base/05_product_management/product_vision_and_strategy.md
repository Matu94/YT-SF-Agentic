# Product Vision & Strategy: Building for Scale

As a Technical Product Manager, my goal is to ensure that every technical credit spent translates into business value. This document explains the strategy behind the YouTube Metrics Pipeline.

## 1. Why Phased Onboarding?
We start with **Phase 1: Fókusz Stúdió**. 
*   **The "Microcosm" Strategy**: By starting with 4 channels under 1 studio, we can perfect the data model and the dbt transformation logic on a small, manageable scale.
*   **The Roadmap**: Once the "Template" is solid, **Phase 2** (Cérnagyár expansion) becomes a "Copy-Paste" operation rather than a re-engineering effort.

## 2. Cost Governance (The EUR 5/Month Rule)
*   **The Problem**: Snowflake is powerful but can be expensive if left unmonitored.
*   **The Solution**: We use **Resource Monitors** and **X-Small warehouses** with aggressive auto-suspend.
*   **Business Impact**: This ensures the project remains a "Hobby" cost-wise while providing "Enterprise" level insights.

## 3. Metadata Hierarchy
*   **Structure**: `Organization > Studio/Creator > Channel`.
*   **Why?**: This hierarchy allows for "Roll-up" reporting. We can see how an individual video performed, how Fókusz Stúdió performed as a whole, or the total reach of the Cérnagyár organization.
*   **Value**: It bridges the gap between "Technical API IDs" and "Business Reality."

## 4. Metric Prioritization
We focus on **Subscribers, Views, Likes, and Comments**.
*   **Why?**: These are the "Core Engagement" metrics. While YouTube provides hundreds of data points, these four give the most immediate "Health Check" of a channel's growth.

---
*Created by **Technical Product Manager** — Visionary & Strategist*
