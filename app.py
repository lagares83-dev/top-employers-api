from flask import Flask, request, jsonify
import requests
import re
import json
from datetime import datetime, timedelta
from collections import Counter

app = Flask(__name__)

BASE_URL = "https://www.top-employers.com"
SEARCH_URL = BASE_URL + "/search-top-employers/"

HEADERS = {"User-Agent": "Mozilla/5.0"}

CACHE_DURATION_HOURS = 24

DATA_CACHE = {
    "ranking": [],
    "last_update": None
}

COMPANIES_BY_COUNTRY_CACHE = {}
COMPANY_CACHE = {}

# ------------------------------------------------
# EXTRAER JSON DEL HTML
# ------------------------------------------------

def extract_fwp_json(html):
    match = re.search(r'window\.FWP_JSON\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        raise Exception("FWP_JSON not found")
    return json.loads(match.group(1))

# ------------------------------------------------
# SCRAPE RANKING
# ------------------------------------------------

def scrape_ranking():

    r = requests.get(SEARCH_URL, headers=HEADERS)
    html = r.text

    fwp = extract_fwp_json(html)

    dropdown_html = fwp["preload_data"]["facets"]["employer_country"]

    pattern = r'<option value="([^"]+)">([^<]+) \((\d+)\)</option>'
    matches = re.findall(pattern, dropdown_html)

    countries = []

    for slug, name, count in matches:

        if slug.strip() == "":
            continue

        countries.append({
            "slug": slug,
            "country": name.strip(),
            "certified_companies": int(count)
        })

    countries.sort(key=lambda x: x["certified_companies"], reverse=True)

    return countries

# ------------------------------------------------
# REFRESH DATA
# ------------------------------------------------

def refresh_data():
    DATA_CACHE["ranking"] = scrape_ranking()
    DATA_CACHE["last_update"] = datetime.utcnow()

def ensure_data_fresh():

    if not DATA_CACHE["ranking"]:
        refresh_data()
        return

    if datetime.utcnow() - DATA_CACHE["last_update"] > timedelta(hours=CACHE_DURATION_HOURS):
        refresh_data()

# ------------------------------------------------
# SCRAPE EMPRESAS POR PAIS
# ------------------------------------------------

def scrape_companies(country_slug, limit):

    url = f"{SEARCH_URL}?_employer_country={country_slug}"

    r = requests.get(url, headers=HEADERS)
    html = r.text

    pattern = r'<h3 class="employer-card__info__name">.*?>(.*?)</a>'
    names = re.findall(pattern, html)

    companies = []

    for n in names[:limit]:

        companies.append({
            "name": n.strip(),
            "country": country_slug
        })

    return companies

# ------------------------------------------------
# SCRAPE EMPRESA
# ------------------------------------------------

def scrape_company(name):

    search_url = f"{SEARCH_URL}?_employer_search={name}"

    r = requests.get(search_url, headers=HEADERS)
    html = r.text

    match = re.search(r'/employer/([^"]+)/', html)

    if not match:
        return None

    slug = match.group(1)

    profile = f"{BASE_URL}/employer/{slug}/"

    r = requests.get(profile, headers=HEADERS)
    html = r.text

    sector_match = re.search(
        r'<li class="employer-branches__item branch-item">([^<]+)</li>',
        html
    )

    sector = sector_match.group(1) if sector_match else None

    countries = re.findall(
        r'<li class="employer-countries__list__item">([^<]+)</li>',
        html
    )

    certifications = []

    if "Global" in html:
        certifications.append("Global")

    if "Europe" in html:
        certifications.append("Europe")

    return {
        "name": name,
        "sector": sector,
        "countries_certified_in": countries,
        "certifications": certifications,
        "total_countries": len(countries),
        "profile_url": profile
    }

# ------------------------------------------------
# METRICAS
# ------------------------------------------------

def compute_metrics():

    ranking = DATA_CACHE["ranking"]

    total_countries = len(ranking)
    total_companies = sum(c["certified_companies"] for c in ranking)

    top_country = ranking[0]

    top3 = sum(c["certified_companies"] for c in ranking[:3]) / total_companies
    top5 = sum(c["certified_companies"] for c in ranking[:5]) / total_companies
    top10 = sum(c["certified_companies"] for c in ranking[:10]) / total_companies

    spain = next(c for c in ranking if c["slug"] == "spain")

    spain_rank = ranking.index(spain) + 1

    spain_share = spain["certified_companies"] / total_companies

    return {
        "total_countries": total_countries,
        "total_companies": total_companies,
        "top_country": top_country,
        "concentration": {
            "top3_share": top3,
            "top5_share": top5,
            "top10_share": top10
        },
        "spain": {
            "rank": spain_rank,
            "certified_companies": spain["certified_companies"],
            "share_global": spain_share
        }
    }

# ------------------------------------------------
# SECTORES
# ------------------------------------------------

def sector_ranking():

    sectors = []

    for company in COMPANY_CACHE.values():

        if company and company["sector"]:
            sectors.append(company["sector"])

    counter = Counter(sectors)

    ranking = []

    for sector, count in counter.most_common():

        ranking.append({
            "sector": sector,
            "companies": count
        })

    return ranking

# ------------------------------------------------
# ENDPOINTS
# ------------------------------------------------

@app.route("/")
def home():

    return jsonify({
        "status": "Top Employers Intelligence Engine",
        "last_update": DATA_CACHE["last_update"]
    })

@app.route("/top-employers/ranking")
def ranking():

    ensure_data_fresh()

    return jsonify(DATA_CACHE["ranking"])

@app.route("/top-employers/metrics")
def metrics():

    ensure_data_fresh()

    return jsonify(compute_metrics())

@app.route("/top-employers/companies")
def companies():

    country = request.args.get("country")
    limit = int(request.args.get("limit", 50))

    key = f"{country}_{limit}"

    if key not in COMPANIES_BY_COUNTRY_CACHE:

        COMPANIES_BY_COUNTRY_CACHE[key] = scrape_companies(country, limit)

    return jsonify(COMPANIES_BY_COUNTRY_CACHE[key])

@app.route("/top-employers/company")
def company():

    name = request.args.get("name")

    key = name.lower()

    if key not in COMPANY_CACHE:

        COMPANY_CACHE[key] = scrape_company(name)

    return jsonify(COMPANY_CACHE[key])

@app.route("/top-employers/sectors")
def sectors():

    return jsonify(sector_ranking())

@app.route("/top-employers/force-update")
def force_update():

    refresh_data()

    return jsonify({
        "message": "dataset refreshed",
        "last_update": DATA_CACHE["last_update"]
    })

# ------------------------------------------------

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
