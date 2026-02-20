from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

BASE_URL = "https://www.top-employers.com/search-top-employers/"

# ===============================
# Extraer todos los países
# ===============================

def get_all_countries():
    response = requests.get(BASE_URL, timeout=15)
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

    # Ordenamos por número descendente
    countries = sorted(countries, key=lambda x: x["certified_companies"], reverse=True)

    return countries


# ===============================
# Extraer datos de un país
# ===============================

def get_country_total(country="spain"):
    countries = get_all_countries()

    for c in countries:
        if c["slug"] == country.lower():
            return c

    raise Exception("Country not found")


# ===============================
# ENDPOINTS
# ===============================

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
    country = request.args.get("country", "spain").lower()

    try:
        data = get_country_total(country)
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

        difference = data1["certified_companies"] - data2["certified_companies"]

        return jsonify({
            "country1": data1,
            "country2": data2,
            "difference": difference
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
