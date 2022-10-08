from datetime import datetime
from flask import Flask, request
import requests
import json
import os

KNACK_API_URL = "https://api.knack.com/v1/objects/"
OBJECT_ID_UAT = "object_180"
KNACK_APP_ID_UAT = os.getenv("KNACK_APP_ID_UAT")
KNACK_API_KEY_UAT = os.getenv("KNACK_API_KEY_UAT")
# todo: get prod object id
OBJECT_ID = "object_180"
KNACK_APP_ID = os.getenv("KNACK_APP_ID")
KNACK_API_KEY = os.getenv("KNACK_API_KEY")

# map knack field ids to human rememberable names
field_maps = {
    "total_amount_uat": "field_3338",
    "payment_status_uat": "field_3352"
    # "payment_status: todo: get field for prod
}

# map citybase payment statuses to knack options
payment_status_map = {
    "successful": "PAID",
    "voided": "VOID",
    "refunded": "REFUND",
    # todo: find out how does citybase send "UNPAID" and "CANCEL"?
}


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
    """
    :param custom_attributes: list of objects {key, object} from citybase
    :return: knack record id string or False if not found
    """
    if len(custom_attributes) < 1:
        return False
    for attribute in custom_attributes:
        if attribute["key"] == "knack_record_id":
            return attribute["value"]
    return False


def get_knack_record_id(citybase_data):
    """
    :param citybase_data: json from POST request
    :return: str, knack record id or tuple(text, resp code), if error
    """
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
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_record_id, str):
        return knack_record_id
    payment_status = citybase_data["data"]["status"]
    knack_payload = json.dumps(
        {field_maps["payment_status"]: payment_status_map[payment_status]}
    )
    # send payment status to knack
    r = requests.put(
        f"{KNACK_API_URL}{OBJECT_ID}/records/{knack_record_id}",
        headers=headers["prod"],
        data=knack_payload,
    )
    if r.status_code == 200:
        return "status updated", r.status_code
    # if unsuccessful, return knack's status response as response
    return r.text, r.status_code


@app.route("/citybase_postback_uat", methods=["POST"])
def handle_postback_uat():
    citybase_data = request.get_json()
    knack_record_id = get_knack_record_id(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_record_id, str):
        return knack_record_id
    payment_status = citybase_data["data"]["status"]
    knack_payload = json.dumps(
        {field_maps["payment_status_uat"]: payment_status_map[payment_status]}
    )
    # send payment status to knack
    r = requests.put(
        f"{KNACK_API_URL}{OBJECT_ID_UAT}/records/{knack_record_id}",
        headers=headers["uat"],
        data=knack_payload,
    )
    if r.status_code == 200:
        return "status updated", r.status_code
    # if unsuccessful, return knack's status response as response
    return r.text, r.status_code


if __name__ == "__main__":
    # todo: remember to turn off debug!
    app.run(debug=True)
