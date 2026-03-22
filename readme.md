# Telegram Mood Tracker Bot

A Telegram bot for structured daily mood tracking with automated phase analysis.

## What this project demonstrates
- Building real Telegram bots with multi-step user interaction
- Integrating external APIs (Google Sheets)
- Processing user input and generating structured data
- Implementing simple decision logic (phase detection)

## Features
- Multi-step conversation flow (sleep, mood, energy, anxiety, etc.)
- Inline and reply keyboards for удобного вводу
- Automatic phase detection (Hypomania / Depression / Mixed / Neutral)
- Data storage in Google Sheets
- Async architecture (python-telegram-bot v20+)

## Tech Stack
- Python
- python-telegram-bot (async)
- Google Sheets API (gspread)
- dotenv (.env for token management)

## Example Flow
User → `/start`  
→ answers questions  
→ data is saved to Google Sheets  
→ phase is calculated automatically  

## Use Cases
- Personal tracking bots
- Simple data collection systems
- Telegram-based automation tools

## Setup
1. Add BOT_TOKEN to `.env`
2. Add `credentials.json` for Google Sheets
3. Run:
```bash
python MoodBot.py