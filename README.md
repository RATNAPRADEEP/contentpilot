# ContentPilot

A zero-cost, automation-first content pipeline.

**Goal:** discover a topic, turn it into a structured short-form video package, render a video, and keep the workflow reusable when the topic changes.

## Current architecture

- Static dashboard: GitHub Pages
- Automation: GitHub Actions
- Data: repository JSON/Markdown artifacts
- Video rendering: FFmpeg on the GitHub Actions runner
- Voice: system TTS on the runner (no paid API)
- Research inputs: public RSS feeds
- Optional later integrations: YouTube upload, richer research, external AI providers

## Zero-cost principle

The core workflow must remain usable without AWS, paid AI APIs, or a paid database.

## First milestone

The system will automatically:
1. collect public feed items
2. score/select a topic
3. create a research/content package
4. generate a vertical 9:16 video
5. publish the generated artifact for download
6. update the dashboard

You should not need to edit source code for normal topic changes.

## Repository

https://github.com/RATNAPRADEEP/contentpilot
