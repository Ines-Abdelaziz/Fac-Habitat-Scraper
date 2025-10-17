import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fach_scraper_core import scrape_fac_habitat

# === CONFIG ===
DEPARTMENTS = ["75", "92", "93", "94", "95", "78", "77"]
SENDER_EMAIL = "ines.abdelaziz19@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  # safer
RECIPIENT_EMAIL = "ines.abdelaziz19@gmail.com"
STATE_FILE = "last_results.csv"
LAST_DAILY_FILE = "last_daily_sent.txt"  # track last daily email date


# === UTILS ===
def send_email(subject, body, html_body=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Fac-Habitat Bot <{SENDER_EMAIL}>"
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


def get_previous_df():
    if os.path.exists(STATE_FILE):
        return pd.read_csv(STATE_FILE)
    return pd.DataFrame()


def save_current_df(df):
    df.to_csv(STATE_FILE, index=False)


def should_send_daily_email():
    today = datetime.now().date()
    if not os.path.exists(LAST_DAILY_FILE):
        return True
    with open(LAST_DAILY_FILE, "r") as f:
        last_sent = f.read().strip()
    return last_sent != str(today)


def update_daily_marker():
    today = datetime.now().date()
    with open(LAST_DAILY_FILE, "w") as f:
        f.write(str(today))


# === MAIN ===
if __name__ == "__main__":
    now = datetime.now()
    print(f"=== Run at {now.strftime('%Y-%m-%d %H:%M:%S')} ===")

    df = scrape_fac_habitat(DEPARTMENTS)
    print(f"Scraped {len(df)} rows")

    previous_df = get_previous_df()
    has_new = False

    if previous_df.empty and not df.empty:
        has_new = True
    elif not previous_df.empty:
        # Compare by a unique column (like 'Residence' or 'Link')
        if "Residence" in df.columns:
            new_rows = df[~df["Residence"].isin(previous_df["Residence"])]
        else:
            new_rows = df[~df.apply(tuple, 1).isin(previous_df.apply(tuple, 1))]
        has_new = not new_rows.empty

    # --- Send new availability email ---
    if has_new:
        html_table = df.to_html(index=False, escape=False)
        send_email(
            subject=f"Fac-Habitat : {len(df)} résidences disponibles (nouvelles détectées)",
            body="De nouvelles disponibilités ont été trouvées :",
            html_body=html_table,
        )
        save_current_df(df)
        print("📧 Sent NEW availability email")

    # --- Send daily summary (once per day) ---
    if should_send_daily_email():
        html_table = df.to_html(index=False, escape=False)
        if df.empty:
            send_email(
                subject=f"Fac-Habitat – Rapport du {now.strftime('%d %B %Y')}",
                body="Aucune résidence disponible aujourd’hui.",
            )
        else:
            send_email(
                subject=f"Fac-Habitat – Rapport du {now.strftime('%d %B %Y')} ({len(df)} dispo)",
                body="Voici le rapport quotidien des résidences disponibles :",
                html_body=html_table,
            )
        update_daily_marker()
        print("🗓️ Sent DAILY summary email")

    if not has_new and not should_send_daily_email():
        print("⏳ No new availabilities — no email sent.")
