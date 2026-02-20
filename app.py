from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "API running"})

@app.route("/top-employers/search")
def search():
    q = request.args.get("q")
    country = request.args.get("country")
    limit = request.args.get("limit", 10)

    return jsonify({
        "query": {"q": q, "country": country, "limit": limit},
        "count": 1,
        "results": [
            {
                "name": "Empresa Demo",
                "profile_url": "https://www.top-employers.com/es/",
                "countries_certified_count": 1,
                "countries_certified": ["España"],
                "sector": "Demo Sector"
            }
        ],
        "source": "top-employers.com",
        "retrieved_at": "2026-02-20"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
