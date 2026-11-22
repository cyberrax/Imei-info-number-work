import os
import hashlib
import requests

from flask import Flask, request, jsonify

app = Flask(__name__)

UPSTREAM_API = "https://viraj-imei-to-information.vercel.app/api/imei"


def generate_demo_number(imei):
    digest = hashlib.sha256(imei.encode()).hexdigest()

    prefix = str(6 + (int(digest[0], 16) % 4))
    suffix = str(int(digest[1:17], 16)).zfill(20)[-9:]

    return "+91" + prefix + suffix


@app.route("/api/imei", methods=["GET"])
def imei_lookup():
    imei = request.args.get("imei_num", "").strip()

    if len(imei) != 15 or not imei.isdigit():
        return jsonify({
            "status": "error",
            "message": "Invalid IMEI"
        }), 400

    api_key = os.getenv("VIRAJ_API_KEY")

    if not api_key:
        return jsonify({
            "status": "error",
            "message": "API configuration missing"
        }), 500

    try:
        response = requests.get(
            UPSTREAM_API,
            params={"imei_num": imei, "key": api_key},
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if data.get("status") != "success":
            return jsonify({
                "status": "error",
                "message": "IMEI API failed"
            }), 502

        result = data.get("result")

        if not isinstance(result, dict):
            return jsonify({
                "status": "error",
                "message": "Invalid upstream response"
            }), 502

        result["mobile_number_demo"] = generate_demo_number(imei)
        result["mobile_number_type"] = "SYNTHETIC - VERIFIED"

        return jsonify({
            "status": "success",
            "result": result,
            "buy_api": "@cyberrax"
        }), 200

    except requests.RequestException:
        return jsonify({
            "status": "error",
            "message": "Upstream API unavailable"
        }), 502

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid upstream JSON"
        }), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
