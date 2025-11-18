import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fach_scraper_core import scrape_fac_habitat
import unicodedata

# === CONFIG ===
DEPARTMENTS = ["75", "92", "93", "94", "95", "78", "77"]
SENDER_EMAIL = "ines.abdelaziz19@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAILS = [
    "ines.abdelaziz19@gmail.com",
    "ihssanboutebicha@gmail.com",
    "ja_boukezzi@esi.dz",
"jf_bentaleb@esi.dz",
"ja_slimane@esi.dz ", 
 "abir.benzaaimia@gmail.com"   
]

# Persist ONLY the stable keys here (not the whole table)
STATE_FILE = "last_results.csv"
LAST_DAILY_FILE = "last_daily_sent.txt"


# === UTILS ===
def send_email(subject, body, html_body=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Fac-Habitat Bot <{SENDER_EMAIL}>"
    msg["To"] = ", ".join(RECIPIENT_EMAILS)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


def _normalize(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())  # collapse spaces


def add_stable_key(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Detect possible column names
    link_col = None
    for candidate in ["Link", "link", "url", "URL"]:
        if candidate in df.columns:
            link_col = candidate
            break

    residence_col = None
    for candidate in ["Residence", "résidence", "titre"]:
        if candidate in df.columns:
            residence_col = candidate
            break

    city_col = None
    for candidate in ["City", "Ville", "ville"]:
        if candidate in df.columns:
            city_col = candidate
            break

    # Priority 1: unique URL
    if link_col:
        df["__key__"] = df[link_col].astype(str).str.strip()
    # Priority 2: Residence + City
    elif residence_col and city_col:
        df["__key__"] = df.apply(
            lambda r: f"{_normalize(r[residence_col])}::{_normalize(r[city_col])}",
            axis=1,
        )
    # Fallback: Residence only
    elif residence_col:
        df["__key__"] = df[residence_col].apply(_normalize)
    else:
        df["__key__"] = df.index.astype(str)

    return df


def load_previous_keys() -> set:
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        prev = pd.read_csv(STATE_FILE)
        # backward compatible: the state file might be a full table from older runs
        if "__key__" in prev.columns:
            return set(prev["__key__"].astype(str))
        # Try to reconstruct keys if old file saved a full df
        prev = add_stable_key(prev)
        return set(prev["__key__"].astype(str))
    except Exception:
        return set()


def save_current_keys(keys: set):
    pd.DataFrame({"__key__": sorted(keys)}).to_csv(STATE_FILE, index=False)


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
    df = add_stable_key(df)
    print(f"Scraped {len(df)} rows")

    current_keys = set(df["__key__"].astype(str))

    previous_keys = load_previous_keys()

    # Compute true "new" residences by key (order/other fields ignored)
    new_keys = current_keys - previous_keys
    has_new = len(new_keys) > 0
    print(
        f"[DEBUG] Current keys: {len(current_keys)}, Previous keys: {len(previous_keys)}, New keys: {len(new_keys)}"
    )
    # --- Send new availability email (only the truly new rows) ---
    if has_new:
        new_rows = df[df["__key__"].isin(new_keys)].drop(columns=["__key__"])
        html_table = new_rows.to_html(index=False, escape=False)
        send_email(
            subject=f"Fac-Habitat : {len(new_rows)} nouvelle(s) résidence(s) disponible(s)",
            body="De nouvelles disponibilités ont été trouvées :",
            html_body=html_table,
        )
        # Save ONLY the current keys snapshot
        save_current_keys(current_keys)
        print(f"📧 Sent NEW availability email for {len(new_rows)} item(s)")

    # --- Send daily summary (once per day) ---
    if should_send_daily_email():
        summary_df = df.drop(columns=["__key__"]) if "__key__" in df.columns else df
        if summary_df.empty:
            send_email(
                subject=f"Fac-Habitat – Rapport du {now.strftime('%d %B %Y')}",
                body="Aucune résidence disponible aujourd’hui.",
            )
        else:
            send_email(
                subject=f"Fac-Habitat – Rapport du {now.strftime('%d %B %Y')} ({len(summary_df)} dispo)",
                body="Voici le rapport quotidien des résidences disponibles :",
                html_body=summary_df.to_html(index=False, escape=False),
            )
        update_daily_marker()
        print("🗓️ Sent DAILY summary email")

    if not has_new and not should_send_daily_email():
        print("⏳ No new availabilities — no email sent.")
