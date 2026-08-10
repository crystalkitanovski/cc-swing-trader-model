# Homework Tracker

A simple, installable web app for tracking 8th grade homework and getting reminded before things are due. No login, no server, no ads — everything is stored privately in your browser on your device.

## Features

- **Add assignments** with subject, title, due date, optional notes, and how many days ahead you want a reminder.
- **Color-coded urgency**: red = overdue/due today, amber = due tomorrow or this week, green = later.
- **Subject filters** to see just Math, Science, etc.
- **Check off** finished homework — it moves to a collapsible "Completed" section.
- **Reminders**: turn on browser notifications and the app will notify you (when it's open, and once a day when you open it) about anything due soon, based on the lead time you set per assignment.
- **Installable (PWA)**: add it to your phone or laptop's home screen/app list so it opens like a real app and works offline.
- **Backup**: export your homework list to a JSON file and import it later (e.g. if you switch devices or clear browser data).

## Running it

This is a static site — no build step, no backend. Two easy options:

### Option A: Open it directly
Open `index.html` in a browser. Everything works except installing as an app and notifications may be limited on `file://` URLs in some browsers.

### Option B: Serve it locally (recommended, enables install + notifications reliably)
```bash
cd homework-tracker
python3 -m http.server 8000
```
Then visit `http://localhost:8000` in your browser.

### Option C: Deploy for free with GitHub Pages
1. Push this repo to GitHub (already done if you're reading this in the repo).
2. In the repo settings, enable **GitHub Pages**, source: branch `main` (or your default branch), folder `/homework-tracker` (or move these files into their own repo/branch root).
3. Visit the published URL on your phone and tap **"Add to Home Screen"** (Safari) or use the install icon in the address bar (Chrome/Edge).

## About reminders — please read

Browsers do **not** allow websites to reliably wake themselves up and send notifications while fully closed (this is a deliberate privacy/battery protection, especially strict on iPhones). So reminders work like this:

- Every time you **open the app**, it checks all your assignments and immediately notifies you (if notifications are on) about anything due within your chosen lead time.
- While the app stays **open in a tab**, it re-checks every 15 minutes.
- It does **not** send notifications while the app is fully closed and your phone is asleep.

**To make sure you never miss anything**, do one (or more) of these:
- Install the app to your home screen and open it once each morning/evening — a habit like checking it after school works great.
- Set a recurring phone alarm/reminder ("Check homework app") at a consistent time.
- Use the color-coded list itself as your source of truth — red items always need attention *today*.

## Data & privacy

All your homework data lives in your browser's `localStorage` on your device only. Nothing is sent to a server. Clearing your browser data will erase it — use **Export backup** periodically if you want a safety copy.

## File overview

- `index.html` – app markup
- `styles.css` – styling (supports light/dark mode automatically)
- `app.js` – all app logic (storage, rendering, reminders)
- `manifest.json` + `icons/` – makes the app installable
- `sw.js` – service worker for offline support
