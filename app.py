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

    try:
        limit = int(limit)
    except:
        limit = 10

    # ---- Lógica dinámica básica ----

    name = "Empresa Demo"
    if q:
        name = f"Empresa Demo - match: {q}"

    countries = ["España"]
    if country:
        countries = [country]

    sector = "Demo Sector"
    if country and country.lower() in ["mexico", "méxico"]:
        sector = "Demo Sector MX"
    elif country and country.lower() == "alemania":
        sector = "Demo Sector DE"

    results = []
    for i in range(min(limit, 3)):
        results.append({
            "name": f"{name} {i+1}",
            "profile_url": "https://www.top-employers.com/es/",
            "countries_certified_count": len(countries),
            "countries_certified": countries,
            "sector": sector
        })

    return jsonify({
        "query": {
            "q": q,
            "country": country,
            "limit": limit
        },
        "count": len(results),
        "results": results,
        "source": "top-employers.com",
        "retrieved_at": "2026-02-20"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
