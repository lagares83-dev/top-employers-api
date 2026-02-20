from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

headers = {
    "User-Agent": "Mozilla/5.0"
}


# ===============================
# Obtener sector desde perfil
# ===============================
def get_sector(profile_url):
    try:
        response = requests.get(profile_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        sector_tag = soup.select_one(".employer-branches__item")

        if sector_tag:
            return sector_tag.text.strip()
        return None
    except Exception:
        return None


# ===============================
# Scrape listado principal
# ===============================
def scrape_top_employers(country="spain", search_term=None, limit=5):

    base_url = "https://www.top-employers.com/search-top-employers/"

    params = {
        "_employer_country": country
    }

    if search_term:
        params["_employer_search"] = search_term

    response = requests.get(base_url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Total real desde el dropdown
    total_real = 0
    options = soup.select("select[data-name='employer_country'] option")
    for option in options:
        if option.get("value") == country:
            text = option.text.strip()
            if "(" in text:
                total_real = int(text.split("(")[1].replace(")", "").strip())

    cards = soup.select("article.employer-card")
    cards = cards[:limit]

    employers = []

    for card in cards:

        name_tag = card.select_one(".employer-card__info__name a")

        if name_tag:
            name = name_tag.text.strip()
            profile_url = name_tag["href"]

            sector = None

            # Solo scrapeamos sector si el límite es pequeño
            if limit <= 20:
                sector = get_sector(profile_url)

            employers.append({
                "name": name,
                "sector": sector,
                "profile_url": profile_url
            })

    return employers, total_real


# ===============================
# Endpoint raíz
# ===============================
@app.route("/")
def home():
    return jsonify({"status": "API running"})


# ===============================
# Endpoint búsqueda empresas
# ===============================
@app.route("/top-employers/search")
def search():

    country = request.args.get("country", "spain").lower()
    q = request.args.get("q")
    limit = int(request.args.get("limit", 5))

    results, total_real = scrape_top_employers(
        country=country,
        search_term=q,
        limit=limit
    )

    return jsonify({
        "total_certified": total_real,
        "returned": len(results),
        "query": {
            "country": country,
            "q": q,
            "limit": limit
        },
        "results": results,
        "source": "top-employers.com"
    })


# ===============================
# Endpoint todos los países
# ===============================
@app.route("/top-employers/countries")
def get_countries():

    base_url = "https://www.top-employers.com/search-top-employers/"
    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    options = soup.select("select[data-name='employer_country'] option")

    countries = []

    for option in options:
        text = option.text.strip()

        if "(" in text and ")" in text:
            name = text.split("(")[0].strip()
            total = int(text.split("(")[1].replace(")", "").strip())

            countries.append({
                "country": name,
                "total_certified": total
            })

    return jsonify({
        "countries": countries,
        "source": "top-employers.com"
    })


# ===============================
# Arranque
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
