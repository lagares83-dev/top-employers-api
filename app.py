from flask import Flask, request, jsonify
import requests
import re
import json
from datetime import datetime, timedelta

app = Flask(__name__)

BASE_URL = "https://www.top-employers.com"
SEARCH_URL = BASE_URL + "/search-top-employers/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ======================================================
# CONFIGURACIÓN CACHE
# ======================================================

CACHE_DURATION_HOURS = 24  # Cambia si quieres menor tiempo

DATA_CACHE = {
    "ranking": [],
    "last_update": None
}

# ======================================================
# UTILIDADES
# ======================================================

def extract_fwp_json(html):
    match = re.search(r'window\.FWP_JSON\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        raise Exception("FWP_JSON not found")
    return json.loads(match.group(1))


def scrape_ranking():
    response = requests.get(SEARCH_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    html = response.text

    fwp = extract_fwp_json(html)

    dropdown_html = fwp["preload_data"]["facets"]["employer_country"]

    pattern = r'<option value="([^"]+)">([^<]+) \((\d+)\)</option>'
    matches = re.findall(pattern, dropdown_html)

    countries = []

    for slug, name, count in matches:
        countries.append({
            "slug": slug,
            "country": name.strip(),
            "certified_companies": int(count)
        })

    countries = sorted(
        countries,
        key=lambda x: x["certified_companies"],
        reverse=True
    )

    return countries


def refresh_data():
    DATA_CACHE["ranking"] = scrape_ranking()
    DATA_CACHE["last_update"] = datetime.utcnow()


def ensure_data_fresh():
    if not DATA_CACHE["ranking"]:
        refresh_data()
        return

    if datetime.utcnow() - DATA_CACHE["last_update"] > timedelta(hours=CACHE_DURATION_HOURS):
        refresh_data()

# ======================================================
# ENDPOINTS
# ======================================================

@app.route("/")
def home():
    return jsonify({
        "status": "Top Employers Competitive Intelligence API",
        "last_update": DATA_CACHE["last_update"]
    })


@app.route("/top-employers/ranking")
def ranking():
    ensure_data_fresh()

    return jsonify({
        "total_countries": len(DATA_CACHE["ranking"]),
        "last_update": DATA_CACHE["last_update"],
        "ranking": DATA_CACHE["ranking"]
    })


@app.route("/top-employers/country")
def country():
    ensure_data_fresh()

    country_slug = request.args.get("country", "spain").lower()

    country_data = next(
        (c for c in DATA_CACHE["ranking"] if c["slug"] == country_slug),
        None
    )

    if not country_data:
        return jsonify({"error": "Country not found"}), 404

    return jsonify(country_data)


@app.route("/top-employers/compare")
def compare():
    ensure_data_fresh()

    c1 = request.args.get("country1")
    c2 = request.args.get("country2")

    if not c1 or not c2:
        return jsonify({"error": "Provide country1 and country2"}), 400

    country1 = next((c for c in DATA_CACHE["ranking"] if c["slug"] == c1.lower()), None)
    country2 = next((c for c in DATA_CACHE["ranking"] if c["slug"] == c2.lower()), None)

    if not country1 or not country2:
        return jsonify({"error": "Country not found"}), 404

    difference = country1["certified_companies"] - country2["certified_companies"]

    return jsonify({
        "country1": country1,
        "country2": country2,
        "difference": difference
    })


@app.route("/top-employers/force-update")
def force_update():
    refresh_data()
    return jsonify({
        "message": "Data refreshed manually",
        "last_update": DATA_CACHE["last_update"]
    })


# ======================================================
# START
# ======================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
