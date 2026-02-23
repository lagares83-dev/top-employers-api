from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

BASE_URL = "https://www.top-employers.com"
SEARCH_URL = BASE_URL + "/search-top-employers/"


# ==========================================
# RANKING PAÍSES
# ==========================================

def get_all_countries():
    response = requests.get(SEARCH_URL, timeout=15)
    response.raise_for_status()
    html = response.text

    pattern = r'<option value="([^"]+)">([^<]+) \((\d+)\)</option>'
    matches = re.findall(pattern, html)

    countries = []

    for value, name, count in matches:
        countries.append({
            "slug": value,
            "country": name.strip(),
            "certified_companies": int(count)
        })

    countries = sorted(countries, key=lambda x: x["certified_companies"], reverse=True)
    return countries


def get_country_total(country="spain"):
    countries = get_all_countries()
    for c in countries:
        if c["slug"] == country.lower():
            return c
    raise Exception("Country not found")


# ==========================================
# EMPRESA
# ==========================================

def search_company_slug(name):
    # buscamos en España por defecto
    response = requests.get(f"{SEARCH_URL}?_employer_search={name}", timeout=15)
    response.raise_for_status()
    html = response.text

    match = re.search(r'/employer/([^"]+)/', html)
    if not match:
        raise Exception("Company not found")

    return match.group(1)


def get_company_data(name):
    slug = search_company_slug(name)
    url = f"{BASE_URL}/employer/{slug}/"

    response = requests.get(url, timeout=15)
    response.raise_for_status()
    html = response.text

    # Sector
    sector_match = re.search(r'branch-item">([^<]+)<', html)
    sector = sector_match.group(1) if sector_match else None

    # Certificaciones
    certifications = []
    if "Global" in html:
        certifications.append("Global")
    if "Europe" in html:
        certifications.append("Europe")
    if "Enterprise" in html:
        certifications.append("Enterprise")

    # Países certificados
    country_pattern = r'data-country="([^"]+)"'
    countries = re.findall(country_pattern, html)
    unique_countries = list(set(countries))

    return {
        "name": name,
        "sector": sector,
        "certifications": certifications,
        "countries_certified_in": unique_countries,
        "total_countries": len(unique_countries),
        "profile_url": url
    }


# ==========================================
# ENDPOINTS
# ==========================================

@app.route("/")
def home():
    return jsonify({"status": "Top Employers Intelligence API running"})


@app.route("/top-employers/countries")
def countries():
    return jsonify(get_all_countries())


@app.route("/top-employers/country")
def country():
    country = request.args.get("country", "spain").lower()
    return jsonify(get_country_total(country))


@app.route("/top-employers/compare")
def compare():
    c1 = request.args.get("country1")
    c2 = request.args.get("country2")

    if not c1 or not c2:
        return jsonify({"error": "Provide country1 and country2"}), 400

    data1 = get_country_total(c1)
    data2 = get_country_total(c2)

    return jsonify({
        "country1": data1,
        "country2": data2,
        "difference": data1["certified_companies"] - data2["certified_companies"]
    })


@app.route("/top-employers/company")
def company():
    name = request.args.get("name")
    if not name:
        return jsonify({"error": "Provide company name"}), 400

    try:
        return jsonify(get_company_data(name))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
