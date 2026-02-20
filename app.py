from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def scrape_top_employers(country="spain", search_term=None):
    base_url = "https://www.top-employers.com/search-top-employers/"

    params = {
        "_employer_country": country
    }

    if search_term:
        params["_employer_search"] = search_term

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(base_url, params=params, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    employers = []

    cards = soup.select("article.employer-card")

    for card in cards:
        name_tag = card.select_one(".employer-card__info__name a")

        if name_tag:
            name = name_tag.text.strip()
            profile_url = name_tag["href"]

            employers.append({
                "name": name,
                "profile_url": profile_url
            })

    return employers


@app.route("/")
def home():
    return jsonify({"status": "API running"})


@app.route("/top-employers/search")
def search():
    country = request.args.get("country", "spain").lower()
    q = request.args.get("q")
    limit = int(request.args.get("limit", 10))

    results = scrape_top_employers(country=country, search_term=q)

    return jsonify({
        "count": min(len(results), limit),
        "query": {
            "country": country,
            "q": q,
            "limit": limit
        },
        "results": results[:limit],
        "source": "top-employers.com"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
