import requests
import pandas as pd
from bs4 import BeautifulSoup


def scrape_fac_habitat(selected_deps):
    url = "https://www.fac-habitat.com/fr/residences/json"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Erreur lors du chargement des données JSON.")

    data = response.json()
    residences = [
        value
        for value in data.values()
        if value.get("cp")[:2] in selected_deps and value.get("gestionnaire") == "FACH"
    ]

    results = []
    base_url = "https://www.fac-habitat.com/fr/residences-etudiantes/id-{id}-{titre_fr}"

    for res in residences:
        url_res = base_url.format(
            id=res["id"], titre_fr=res["titre_fr"].lower().replace(" ", "-")
        )
        html = requests.get(url_res)
        if html.status_code != 200:
            continue

        soup = BeautifulSoup(html.text, "html.parser")
        iframe = soup.find("iframe", class_="reservation")
        if not iframe:
            continue

        iframe_url = iframe["src"]
        iframe_html = requests.get(iframe_url)
        if iframe_html.status_code != 200:
            continue

        iframe_soup = BeautifulSoup(iframe_html.text, "html.parser")
        text = iframe_soup.get_text()

        if "Disponibilité immédiate" in text or "Disponibilité à venir" in text:
            price = soup.find("em", itemprop="lowPrice").find("strong").text
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
