from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

headers = {
    "User-Agent": "Mozilla/5.0"
}


def get_sector(profile_url):
    try:
        response = requests.get(profile_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        sector_tag = soup.select_one(".employer-branches__item")

        if sector_tag:
            return sector_tag.text.strip()
        else:
            return None
    except Exception:
        return None


def scrape_top_employers(country="spain", search_term=None, limit=5):

    base_url = "https://www.top-employers.com/search-top-employers/"

    params = {
        "_employer_country": country
    }

    if search_term:
        params["_employer_search"] = search_term

    response = requests.get(base_url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    cards = soup.select("article.employer-card")
    total_available = len(cards)

    employers = []

    cards = cards[:limit]

    for card in cards:

        name_tag = card.select_one(".employer-card__info__name a")

        if name_tag:
            name = name_tag.text.strip()
            profile_url = name_tag["href"]

            sector = None

            # Solo scrapeamos sector si el límite es razonable
            if limit <= 20:
                sector = get_sector(profile_url)

            employers.append({
                "name": name,
                "sector": sector,
                "profile_url": profile_url
            })

    return employers, total_available


@app.route("/")
def home():
    return jsonify({"status": "API running"})


@app.route("/top-employers/search")
def search():
    country = request.args.get("country", "spain").lower()
    q = request.args.get("q")
    limit = int(request.args.get("limit", 5))

    results, total_available = scrape_top_employers(
        country=country,
        search_term=q,
        limit=limit
    )

    return jsonify({
        "total_certified": total_available,
        "returned": len(results),
        "query": {
            "country": country,
            "q": q,
            "limit": limit
        },
        "results": results,
        "source": "top-employers.com"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
