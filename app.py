from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

FACET_ENDPOINT = "https://www.top-employers.com/wp-json/facetwp/v1/refresh"


def get_country_data(country="spain"):
    payload = {
        "facets": {
            "employer_country": country
        },
        "paged": 1
    }

    response = requests.post(FACET_ENDPOINT, json=payload)
    response.raise_for_status()

    data = response.json()

    pager = data.get("settings", {}).get("pager", {})

    return {
        "country": country,
        "certified_companies": pager.get("total_rows"),
        "total_global": pager.get("total_rows_unfiltered"),
        "per_page": pager.get("per_page"),
        "total_pages": pager.get("total_pages")
    }


@app.route("/")
def home():
    return jsonify({"status": "Top Employers API running"})


@app.route("/top-employers/country")
def country_info():
    country = request.args.get("country", "spain").lower()

    try:
        result = get_country_data(country)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
