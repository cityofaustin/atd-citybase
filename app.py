from datetime import datetime
from flask import Flask, request
from datetime import date
import requests
import json
import os

KNACK_API_URL = "https://api.knack.com/v1/objects/"
TRANSACTIONS_OBJECT_ID_UAT = "object_180"
MESSAGES_OBJECT_ID_UAT = "object_181"
KNACK_APP_ID_UAT = os.getenv("KNACK_APP_ID_UAT")
KNACK_API_KEY_UAT = os.getenv("KNACK_API_KEY_UAT")
# todo: get prod object id
TRANSACTIONS_OBJECT_ID = "object_180"
MESSAGES_OBJECT_ID = "object_181"
KNACK_APP_ID = os.getenv("KNACK_APP_ID")
KNACK_API_KEY = os.getenv("KNACK_API_KEY")

# map knack field ids to human rememberable names
field_maps = {
    "uat": {
        "total_amount": "field_3338",
        "payment_status": "field_3352",
        "invoice_id": "field_3333",
        "created_date": "field_3320",
        "transaction_paid_date": "field_3366",
        "messages_invoice_id": "field_3365",
        "messages_created_date": "field_3369",
        "messages_status": "field_3367",
        "messages_citybase_id": "field_3378"
    },
    "prod": {  # todo update with prod info
        "total_amount": "field_3338",
        "payment_status": "field_3352",
    },
}

# map citybase payment statuses to knack options
payment_status_map = {
    "successful": "PAID",
    "voided": "VOID",
    "refunded": "REFUND",
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


def get_custom_attribute(custom_attributes, attribute_name):
    """
    :param custom_attributes: list of objects {key, object} from citybase
    :param attribute_name: string, which attribute we are fetching
    :return: knack record id string or False if not found
    """
    if len(custom_attributes) < 1:
        return False
    for attribute in custom_attributes:
        if attribute["key"] == attribute_name:
            return attribute["value"]
    return False


def get_knack_record_id(citybase_data):
    """
    :param citybase_data: json from POST request
    :return: str, knack record id or tuple(text, resp code), if error
    """
    try:
        knack_record_id = get_custom_attribute(
            citybase_data["data"]["custom_attributes"], "knack_record_id"
        )
    except KeyError:
        return "Missing custom attributes", 400
    if not knack_record_id:
        return "Missing knack record id custom attribute", 400
    return knack_record_id


def get_knack_invoice(citybase_data):
    """
    :param citybase_data: json from POST request
    :return: str, knack record id or tuple(text, resp code), if error
    """
    try:
        knack_invoice = get_custom_attribute(
            citybase_data["data"]["custom_attributes"], "invoice_number"
        )
    except KeyError:
        return "Missing custom attributes", 400
    if not knack_invoice:
        return "Missing knack invoice number custom attribute", 400
    return knack_invoice


def get_knack_payload(
    environment, payment_status, payment_amount, knack_invoice, today_date
):
    """
    :param environment: "uat" or "prod" depending on which endpoint calls this function
    :param payment_status: info from citybase payload
    :param payment_amount: string amount from citybase payload
    :param knack_invoice: info from citybase payload
    :param today_date: mm/dd/YYYY date string
    :return: json object to send along with PUT or POST
    """
    if payment_status == "refunded":
        return json.dumps(
            {
                field_maps[environment]["payment_status"]: payment_status_map[
                    payment_status
                ],
                field_maps[environment]["invoice_id"]: knack_invoice,
                # if it is a refund, store negative amount
                field_maps[environment]["total_amount"]: f"-{payment_amount}",
                field_maps[environment]["created_date"]: today_date,
            }
        )
    else:
        return json.dumps(
            {
                field_maps[environment]["payment_status"]: payment_status_map[
                    payment_status
                ],
                field_maps[environment]["transaction_paid_date"]: today_date,
            }
        )


def create_message_json(
    environment, citybase_id, today_date, knack_invoice, payment_status
):
    """

    :param environment:
    :param citybase_id:
    :param today_date:
    :param knack_invoice:
    :param payment_status:
    :return:
    """
    return json.dumps(
        {
            field_maps[environment]["messages_invoice_id"]: knack_invoice,
            field_maps[environment]["messages_created_date"]: today_date,
            field_maps[environment]["messages_status"]: payment_status,
            field_maps[environment]["messages_citybase_id"]: citybase_id,
        }
    )


@app.route("/")
def index():
    now = datetime.now().isoformat()
    return f"Austin Transportation Department Citybase healthcheck {now}"


@app.route("/citybase_postback", methods=["POST"])
def handle_postback():
    today_date = date.today().strftime("%m/%d/%Y")
    citybase_data = request.get_json()
    knack_record_id = get_knack_record_id(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_record_id, str):
        return knack_record_id
    knack_invoice = get_knack_invoice(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_invoice, str):
        return knack_invoice
    payment_status = citybase_data["data"]["status"]
    payment_amount = citybase_data["data"]["total_amount"]
    # get json payload for knack
    knack_payload = get_knack_payload(
        "prod", payment_status, payment_amount, knack_invoice
    )
    # if a refund, post a new record to knack transactions table
    if payment_status == "refunded":
        knack_response = requests.post(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/",
            headers=headers["prod"],
            data=knack_payload,
        )
    # otherwise, update existing record payment status
    else:
        knack_response = requests.put(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/{knack_record_id}",
            headers=headers["prod"],
            data=knack_payload,
        )
    if knack_response.status_code == 200:
        return "Payment status updated", knack_response.status_code
    # if unsuccessful, return knack's status response as response
    return knack_response.text, knack_response.status_code


@app.route("/citybase_postback_uat", methods=["POST"])
def handle_postback_uat():
    today_date = date.today().strftime("%m/%d/%Y")
    citybase_data = request.get_json()

    knack_record_id = get_knack_record_id(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_record_id, str):
        return knack_record_id

    knack_invoice = get_knack_invoice(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_invoice, str):
        return knack_invoice

    payment_status = citybase_data["data"]["status"]
    payment_amount = citybase_data["data"]["total_amount"]
    citybase_id = citybase_data["data"]["id"]

    message_payload = create_message_json(
        "uat", citybase_id, today_date, knack_invoice, payment_status
    )
    requests.post(
        f"{KNACK_API_URL}{MESSAGES_OBJECT_ID_UAT}/records/",
        headers=headers["uat"],
        data=message_payload,
    )

    # get json payload for knack transactions table
    knack_payload = get_knack_payload(
        "uat", payment_status, payment_amount, knack_invoice, today_date
    )
    # if a refund, post a new record to knack transactions table
    if payment_status == "refunded":
        knack_response = requests.post(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID_UAT}/records/",
            headers=headers["uat"],
            data=knack_payload,
        )
    # otherwise, update existing record payment status
    else:
        knack_response = requests.put(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID_UAT}/records/{knack_record_id}",
            headers=headers["uat"],
            data=knack_payload,
        )
    if knack_response.status_code == 200:
        return "Payment status updated", knack_response.status_code
    # if unsuccessful, return knack's status response as response
    return knack_response.text, knack_response.status_code


if __name__ == "__main__":
    # todo: remember to turn off debug!
    app.run(debug=True, host="0.0.0.0")
