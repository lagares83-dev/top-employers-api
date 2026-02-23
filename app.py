from flask import Flask, request, jsonify
import requests
import re
import json

app = Flask(__name__)

BASE_URL = "https://www.top-employers.com"
SEARCH_URL = BASE_URL + "/search-top-employers/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ======================================================
# EXTRAER FWP_JSON DEL HTML
# ======================================================

def extract_fwp_json(html):
    match = re.search(r'window\.FWP_JSON\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not match:
        raise Exception("FWP_JSON not found")

    json_text = match.group(1)
    return json.loads(json_text)


# ======================================================
# RANKING PAÍSES
# ======================================================

def get_all_countries():
    response = requests.get(SEARCH_URL, headers=HEADERS, timeout=20)
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


def get_country_total(country_slug):
    countries = get_all_countries()

    for c in countries:
        if c["slug"] == country_slug.lower():
            return c

    raise Exception("Country not found")


# ======================================================
# EMPRESA
# ======================================================

def search_company_slug(name):
    response = requests.get(
        f"{SEARCH_URL}?_employer_search={name}",
        headers=HEADERS,
        timeout=20
    )
    response.raise_for_status()
    html = response.text

    match = re.search(r'/employer/([^"]+)/', html)

    if not match:
        raise Exception("Company not found")

    return match.group(1)


def get_company_data(name):
    slug = search_company_slug(name)
    url = f"{BASE_URL}/employer/{slug}/"

    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    html = response.text

    # ===== SECTOR =====
    sector_match = re.search(
        r'<li class="employer-branches__item branch-item">([^<]+)</li>',
        html
    )
    sector = sector_match.group(1).strip() if sector_match else None

    # ===== CERTIFICACIONES =====
    certifications = []
    if "Global" in html:
        certifications.append("Global")
    if "Europe" in html:
        certifications.append("Europe")
    if "Enterprise" in html:
        certifications.append("Enterprise")

    # ===== PAÍSES =====
    countries = re.findall(
        r'<li class="employer-countries__list__item">([^<]+)</li>',
        html
    )

    unique_countries = list(set(countries))

    return {
        "name": name,
        "sector": sector,
        "certifications": certifications,
        "countries_certified_in": unique_countries,
        "total_countries": len(unique_countries),
        "profile_url": url
    }


# ======================================================
# ENDPOINTS
# ======================================================

@app.route("/")
def home():
    return jsonify({"status": "Top Employers Intelligence API running"})


@app.route("/top-employers/countries")
def countries():
    try:
        data = get_all_countries()
        return jsonify({
            "total_countries": len(data),
            "ranking": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/top-employers/country")
def country():
    country_slug = request.args.get("country", "spain").lower()

    try:
        data = get_country_total(country_slug)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/top-employers/compare")
def compare():
    c1 = request.args.get("country1")
    c2 = request.args.get("country2")

    if not c1 or not c2:
        return jsonify({"error": "Provide country1 and country2"}), 400

    try:
        data1 = get_country_total(c1)
        data2 = get_country_total(c2)

        return jsonify({
            "country1": data1,
            "country2": data2,
            "difference": data1["certified_companies"] - data2["certified_companies"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/top-employers/company")
def company():
    name = request.args.get("name")

    if not name:
        return jsonify({"error": "Provide company name"}), 400

    try:
        data = get_company_data(name)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
