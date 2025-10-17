# 🏢 Fac-Habitat Scraper & Notifier
This project automatically scrapes data from the **Fac-Habitat** website to check the availability of student residences in **Île-de-France**.  
It then sends **email notifications** for:
- 🚨 **New availabilities** (detected every 30 minutes)  
- 🗓️ **Daily summary reports** (sent once per day, even if there are no new availabilities)
All runs are automated using **GitHub Actions (free)** — no server needed.
---
## ✨ Features
- Scrapes all Fac-Habitat residences in selected departments  
- Detects when new availabilities appear  
- Sends two types of automated emails:
  - **Instant alerts** for new availabilities  
  - **Daily summary** every morning  
- Saves last known results in `last_results.csv`  
- 100% server-free automation via **GitHub Actions**
---
## 🧰 Prerequisites
Make sure you have the following:
- Python 3.10 or newer  
- Gmail account with an **App Password** (used for sending emails)  
  > You can create one at [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)  
  > (Requires 2-Step Verification to be enabled.)
Required Python packages:
```bash
pip install -r requirements.txt
```
---
## ⚙️ Configuration
Edit the configuration variables at the top of `fac_habitat_notifier.py` if needed:
```python
DEPARTMENTS = ["75", "92", "93", "94", "95", "78", "77"]
SENDER_EMAIL = "your.email@gmail.com"
RECIPIENT_EMAIL = "recipient@gmail.com"
```
Your Gmail **App Password** should be stored in an environment variable (never in code):
**macOS / Linux:**
```bash
export SENDER_PASSWORD="your_app_password_here"
```
**Windows (PowerShell):**
```powershell
setx SENDER_PASSWORD "your_app_password_here"
```
---
## 🚀 Running Locally
To test the script manually:
```bash
python fac_habitat_notifier.py
```
It will:
- Scrape available residences
- Send an email report
- Detect and notify if new availabilities appear
- Update state files:  
  - `last_results.csv` — last known residences  
  - `last_daily_sent.txt` — last daily email date  
---
## 🤖 Running Automatically (Server-Free)
You can fully automate this with **GitHub Actions**.
### 1. Push your code to GitHub
```bash
git add .
git commit -m "Add notifier automation"
git push origin main
```
### 2. Add your Gmail App Password as a secret
In your GitHub repo:
- Go to **Settings → Secrets and variables → Actions → New repository secret**
- Name: `SENDER_PASSWORD`
- Value: your Gmail App Password
### 3. Verify the workflow
Make sure the file `.github/workflows/fac-habitat.yml` exists with this schedule:
```yaml
on:
  schedule:
    - cron: "*/30 * * * *"   # runs every 30 minutes
```
GitHub will now:
- Run the scraper every 30 minutes  
- Send an instant alert if new availabilities are detected  
- Send one daily summary email per day
You can also trigger it manually from the **Actions** tab in GitHub.
---
## 🗓️ Customize the Daily Email Time
If you want the daily email to be sent at a specific time (for example, **8:00 AM Paris time**),  
you can add another scheduled job in your GitHub Actions file:
```yaml
on:
  schedule:
    - cron: "0 7 * * *"   # runs daily at 8:00 AM Paris time (7 AM UTC)
    - cron: "*/30 * * * *" # every 30 minutes for new availabilities
```
> 🕒 Note: GitHub cron times use **UTC**, so adjust accordingly (Paris = UTC+1 / +2 with DST).
---
## 🗂️ Project Structure
```
fac-habitat-scraper/
├── fac_habitat_notifier.py     # main script (scraper + email notifier)
├── fach_scraper_core.py        # scraping logic
├── requirements.txt
├── last_results.csv            # saved state of previous results
├── last_daily_sent.txt         # marker for daily email
└── .github/
    └── workflows/
        └── fac-habitat.yml     # GitHub Actions automation
```
---
## 📧 Email Behavior Summary
| Email Type | Trigger | Condition | Example Subject |
|-------------|----------|------------|------------------|
| 🚨 New Availability | Every 30 min | Only when new residences appear | `Fac-Habitat : 2 nouvelles résidences disponibles` |
| 🗓️ Daily Summary | Once per day | Always | `Fac-Habitat – Rapport du 17 octobre 2025 (12 dispo)` |
---
## 🧑‍💻 Authors
Originally developed by [Rayane Lark](https://github.com/RayaneLark),  
extended by [Ines Abdelaziz](https://github.com/Ines-Abdelaziz) for automation and daily email notifications.
