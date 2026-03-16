#!/usr/bin/env python3
"""
Enkel webapp for å logge inn på Oda og legge ingredienser fra Google Drive i handlekurven.

Kjør:
    pip install flask requests
    python oda_web.py

Åpne nettleseren på: http://localhost:5000
"""

import json
import os
import re
import subprocess

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.secret_key = os.urandom(24)

MCP_ODA_CMD = ["npx", "--yes", "github:gbbirkisson/mcp-oda"]


def run_mcp_oda(args: list, capture_json: bool = True):
    cmd = MCP_ODA_CMD + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Ukjent feil fra mcp-oda")
    if not capture_json or not result.stdout.strip():
        return None
    return json.loads(result.stdout)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"ok": False, "error": "Brukernavn og passord kreves"}), 400
    try:
        run_mcp_oda(
            ["auth", "login", "--user", username, "--pass", password],
            capture_json=False,
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/fetch-recipe", methods=["POST"])
def fetch_recipe():
    data = request.json
    url = data.get("url", "").strip()

    # Extract Google Drive file ID from sharing link
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        return jsonify({"ok": False, "error": "Ugyldig Google Drive-lenke. Forventet format: drive.google.com/file/d/..."}), 400

    file_id = match.group(1)
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

    try:
        resp = requests.get(download_url, timeout=15)
        resp.raise_for_status()
        lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
        if not lines:
            return jsonify({"ok": False, "error": "Filen er tom eller kunne ikke leses"}), 400
        return jsonify({"ok": True, "ingredients": lines})
    except requests.HTTPError as e:
        return jsonify({"ok": False, "error": f"Kunne ikke hente fil: {e}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/add-to-cart", methods=["POST"])
def add_to_cart():
    data = request.json
    ingredients = data.get("ingredients", [])
    if not ingredients:
        return jsonify({"ok": False, "error": "Ingen ingredienser valgt"}), 400

    results = []
    for ingredient in ingredients:
        try:
            raw = run_mcp_oda(["product", "search", ingredient])
            if isinstance(raw, dict):
                products = raw.get("items", [])
            elif isinstance(raw, list):
                products = raw
            else:
                products = []

            if not products:
                results.append({"ingredient": ingredient, "ok": False, "error": "Ingen treff på Oda"})
                continue

            def sort_key(p):
                rp = p.get("relative_price")
                return rp if rp is not None else p.get("price", float("inf"))

            cheapest = min(products, key=sort_key)
            product_id = cheapest.get("id")

            if not product_id:
                results.append({"ingredient": ingredient, "ok": False, "error": "Mangler produkt-ID"})
                continue

            run_mcp_oda(["product", "add", str(product_id)], capture_json=False)
            results.append({
                "ingredient": ingredient,
                "ok": True,
                "product": cheapest.get("name", ""),
                "price": cheapest.get("price"),
            })

        except Exception as e:
            results.append({"ingredient": ingredient, "ok": False, "error": str(e)})

    return jsonify({"ok": True, "results": results})


if __name__ == "__main__":
    print("Åpne nettleseren på: http://localhost:5000")
    app.run(debug=True, port=5000)
