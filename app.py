from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

BASE_URL = "https://www.top-employers.com/search-top-employers/"


def get_country_total(country="spain"):
    url = f"{BASE_URL}?_employer_country={country}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    html = response.text

    # Buscamos patrón tipo: Spain (146)
    pattern = rf'{country.capitalize()} \((\d+)\)'
    match = re.search(pattern, html)

    if not match:
        raise Exception("Country count not found")

    total = int(match.group(1))

    # También sacamos total global
    global_match = re.search(r'"total_rows_unfiltered":(\d+)', html)
    total_global = int(global_match.group(1)) if global_match else None

    return {
        "country": country,
        "certified_companies": total,
        "total_global": total_global
    }


@app.route("/")
def home():
    return jsonify({"status": "Top Employers API running"})


@app.route("/top-employers/country")
def country_info():
    country = request.args.get("country", "spain").lower()

    try:
        result = get_country_total(country)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
