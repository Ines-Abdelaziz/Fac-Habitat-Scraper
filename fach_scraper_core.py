import requests
import pandas as pd
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def scrape_fac_habitat(selected_deps):
    session = requests.Session()

    retries = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    session.mount("https://", HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        )
    }

    url = "https://www.fac-habitat.com/fr/residences/json"

    try:
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erreur lors du chargement des données JSON : {e}")

    data = response.json()

    residences = [
        value
        for value in data.values()
        if value.get("cp", "")[:2] in selected_deps
        and value.get("gestionnaire") == "FACH"
    ]

    results = []
    base_url = "https://www.fac-habitat.com/fr/residences-etudiantes/id-{id}-{titre_fr}"

    for res in residences:
        url_res = base_url.format(
            id=res["id"],
            titre_fr=res["titre_fr"].lower().replace(" ", "-"),
        )

        try:
            html = session.get(url_res, headers=headers, timeout=15)
            if html.status_code != 200:
                continue
        except requests.exceptions.RequestException:
            continue

        soup = BeautifulSoup(html.text, "html.parser")
        iframe = soup.find("iframe", class_="reservation")
        if not iframe or not iframe.get("src"):
            continue

        iframe_url = iframe["src"]

        try:
            iframe_html = session.get(iframe_url, headers=headers, timeout=15)
            if iframe_html.status_code != 200:
                continue
        except requests.exceptions.RequestException:
            continue

        iframe_soup = BeautifulSoup(iframe_html.text, "html.parser")
        text = iframe_soup.get_text()

        if "Disponibilité immédiate" in text or "Disponibilité à venir" in text:
            price_tag = soup.find("em", itemprop="lowPrice")
            price = (
                price_tag.find("strong").text
                if price_tag and price_tag.find("strong")
                else None
            )

            dispo = (
                "Disponibilité immédiate"
                if "Disponibilité immédiate" in text
                else "Disponibilité à venir"
            )

            results.append(
                {
                    "titre": res["titre_fr"],
                    "ville": res["ville"],
                    "cp": res["cp"],
                    "prix": price,
                    "url": url_res,
                    "email": res.get("email"),
                    "tel": res.get("tel"),
                    "disponibilité": dispo,
                }
            )

    return pd.DataFrame(results)
