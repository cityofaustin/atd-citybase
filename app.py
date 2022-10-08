from datetime import datetime
from flask import Flask, request
import requests
import json
import os

field_maps = {
    "total_amount": "field_3338",
    "payment_status_uat": "field_3352"
    # "payment_status: todo: get field for prod
}

payment_status_map = {
    "successful": "PAID",
    "voided": "VOID",
    "refunded": "REFUND",
    # how does citybase send "UNPAID" and "CANCEL"?
}


KNACK_API_URL = "https://api.knack.com/v1/objects/"
OBJECT_ID_UAT = "object_180"
KNACK_APP_ID_UAT = os.getenv("KNACK_APP_ID_UAT")
KNACK_API_KEY_UAT = os.getenv("KNACK_API_KEY_UAT")
# todo: get prod object id
OBJECT_ID = "object_180"
KNACK_APP_ID = os.getenv("KNACK_APP_ID")
KNACK_API_KEY = os.getenv("KNACK_API_KEY")

headers = {
    "uat": {
        "X-Knack-Application-Id": KNACK_APP_ID_UAT,
        "X-Knack-REST-API-Key": KNACK_API_KEY_UAT,
        "Content-Type": "application/json",
    },
    "prod": {
        "X-Knack-Application-Id": KNACK_APP_ID,
        "X-Knack-REST-API-Key": KNACK_API_KEY,
        "Content-Type": "application/json",
    },
}

app = Flask(__name__)


def get_record_id(custom_attributes):
    if len(custom_attributes) < 1:
        return False
    for attribute in custom_attributes:
        if attribute["key"] == "knack_record_id":
            return attribute["value"]
    return False


def get_knack_record_id(citybase_data):
    try:
        knack_record_id = get_record_id(citybase_data["data"]["custom_attributes"])
    except KeyError:
        return "Missing custom attributes", 400
    if not knack_record_id:
        return "Missing knack record id custom attribute", 400
    return knack_record_id


@app.route("/")
def index():
    now = datetime.now().isoformat()
    return f"ATD Citybase healthcheck {now}"


@app.route("/citybase_postback", methods=["POST"])
def handle_postback():
    citybase_data = request.get_json()
    knack_record_id = get_knack_record_id(citybase_data)
    if not isinstance(knack_record_id, str):
        return knack_record_id
    payment_status = citybase_data["data"]["status"]
    knack_payload = json.dumps(
        {field_maps["payment_status"]: payment_status_map[payment_status]}
    )
    r = requests.put(
        f"{KNACK_API_URL}{OBJECT_ID}/records/{knack_record_id}",
        headers=headers["prod"],
        data=knack_payload,
    )

    return r.text, r.status_code


@app.route("/citybase_postback_uat", methods=["POST"])
def handle_postback_uat():
    citybase_data = request.get_json()
    knack_record_id = get_knack_record_id(citybase_data)
    if not isinstance(knack_record_id, str):
        return knack_record_id
    payment_status = citybase_data["data"]["status"]
    knack_payload = json.dumps(
        {field_maps["payment_status_uat"]: payment_status_map[payment_status]}
    )
    r = requests.put(
        f"{KNACK_API_URL}{OBJECT_ID}/records/{knack_record_id}",
        headers=headers["uat"],
        data=knack_payload,
    )

    return r.text, r.status_code


if __name__ == "__main__":
    app.run(debug=True)
