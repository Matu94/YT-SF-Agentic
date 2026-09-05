# YouTube Data API v3: The Data Source Engine

This document explains the core concepts of the YouTube Data API v3, which serves as the primary data source for our analytics pipeline. Understanding how this API structures its data and charges for usage is critical for efficient pipeline design.

## 1. The Core Concept: REST and JSON
The YouTube Data API is a **RESTful API**. This means we interact with it by sending HTTP requests (like navigating to a webpage) to specific URLs (endpoints). 
*   **Request**: We send a `GET` request containing our API Key and the ID of the channel or video we want.
*   **Response**: YouTube returns the data in **JSON (JavaScript Object Notation)** format, which is a nested, dictionary-like structure perfect for Snowflake's `VARIANT` column.

## 2. The "Part" System (Crucial for Optimization)
Unlike many APIs that return *everything* about an object when you ask for it, YouTube forces you to be specific to save bandwidth and compute power.

You must specify the `part` parameter in your request. A "part" is a cluster of related data:
*   **`snippet`**: Contains basic metadata (Title, Description, Published Date, Channel Name).
*   **`statistics`**: Contains the numbers we care about (View Count, Subscriber Count, Like Count).
*   **`contentDetails`**: Contains information about the actual content (e.g., the length of a video).

**Project Example**: 
When we query a channel, our URL looks like this: 
`.../channels?part=snippet,statistics&id=UC123...`
This tells YouTube: *"Give me the basic info AND the view/subscriber counts for this ID."*

## 3. The Quota System (The Invisible Budget)
The YouTube API is free, but it is strictly rate-limited using a "Quota" system. Every project gets a default of **10,000 quota units per day**.

Different actions cost different amounts of quota:
*   **Read Operation (e.g., fetching channel stats by ID)**: Costs **1 unit**.
*   **Search Operation (e.g., searching for "Snowflake tutorials")**: Costs **100 units**.
*   **Video Uploads**: Cost **1,600 units**.

**Our Strategy**: 
Because Search is so expensive, we *never* search for channels by name in our pipeline. We maintain a static `channels_hierarchy.csv` seed file containing the exact Channel IDs. Fetching stats for 100 channels by ID only costs 100 units, leaving us 9,900 units for other tasks!

## 4. Pagination: Handling Large Results
If a channel has 1,000 videos, the API will not return them all at once (to prevent crashing). It uses **Pagination**.
*   It returns the first 50 results (the max page size).
*   It also returns a `nextPageToken` (e.g., `"CAoQAA"`).
*   To get the next 50, you must make a *new* request, adding `&pageToken=CAoQAA` to the URL.
*   *Note: Our Snowpark Python extraction procedure must include a `while` loop to handle this pagination automatically when we eventually pull video-level data.*

## 5. How It Connects to Snowflake
We do not use an external server (like AWS Lambda) to call the API. We do it natively:
1.  **Network Rule**: Tells Snowflake it's allowed to talk to `youtube.googleapis.com`.
2.  **Secret**: Stores our API Key safely.
3.  **Snowpark (Python)**: Our `01_youtube_extraction.sql` procedure uses the Python `requests` library to call the API directly from within the virtual warehouse, parsing the JSON and dropping it straight into our `LANDING` layer.

---
*Created by **Data Engineer** — Precision Builder*
