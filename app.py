from datetime import datetime
from flask import Flask, request
import requests
import json
import os

KNACK_API_URL = "https://api.knack.com/v1/objects/"
# uat objects
KNACK_APP_ID_UAT = os.getenv("KNACK_APP_ID_UAT")
KNACK_API_KEY_UAT = os.getenv("KNACK_API_KEY_UAT")
TRANSACTIONS_OBJECT_ID_UAT = "object_180"
MESSAGES_OBJECT_ID_UAT = "object_181"
OTS_OBJECT_ID_UAT = "object_164"
LPB_OBJECT_ID_UAT = "object_161"
# prod objects
KNACK_APP_ID = os.getenv("KNACK_APP_ID")
KNACK_API_KEY = os.getenv("KNACK_API_KEY")
TRANSACTIONS_OBJECT_ID = "object_180"
MESSAGES_OBJECT_ID = "object_181"
OTS_OBJECT_ID = "object_164"
LPB_OBJECT_ID = "object_161"

# map knack field ids to human rememberable names
field_maps = {
    "uat": {
        "total_amount": "field_3338",
        "payment_status": "field_3352",
        "invoice_id": "field_3333",
        "created_date": "field_3320",
        "transaction_paid_date": "field_3366",
        "messages_invoice_id": "field_3365",
        "messages_connected_invoice": "field_3372",
        "messages_created_date": "field_3369",
        "messages_status": "field_3367",
        "messages_citybase_id": "field_3378",
        "ots_connection_field": "field_3327",
        "ots_application_status": "field_2862",  # in banner_reservations object
        "ots_paid_status": "field_2858",  # in banner_reservations object
        "ots_payment_date": "field_3144",  # in banner_reservations object
        "lpb_connection_field": "field_3326",
        "lpb_application_status": "field_2796",  # in banner_reservations object
        "lpb_paid_status": "field_2808",  # in banner_reservations object
        "lpb_payment_date": "field_2809",  # in banner_reservations object
    },
    "prod": {
        "total_amount": "field_3342",
        "payment_status": "field_3353",
        "invoice_id": "field_3327",
        "created_date": "field_3320",
        "transaction_paid_date": "field_3352",
        "messages_invoice_id": "field_3363",
        "messages_connected_invoice": "field_3369",
        "messages_created_date": "field_3366",
        "messages_status": "field_3361",
        "messages_citybase_id": "field_3368",
        "ots_connection_field": "field_3329",
        "ots_application_status": "field_2862",  # in banner_reservations object
        "ots_paid_status": "field_2858",  # in banner_reservations object
        "ots_payment_date": "field_3144",  # in banner_reservations object
        "lpb_connection_field": "field_3328",
        "lpb_application_status": "field_2796",  # in banner_reservations object
        "lpb_paid_status": "field_2808",  # in banner_reservations object
        "lpb_payment_date": "field_2809",  # in banner_reservations object
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


def get_knack_payload(environment, payment_status, today_date):
    """
    :param environment: "uat" or "prod" depending on which endpoint calls this function
    :param payment_status: info from citybase payload
    :param today_date: mm/dd/YYYY H:M datetime string
    :return: json object to send along with PUT call to knack
    """
    return json.dumps(
        {
            field_maps[environment]["payment_status"]: payment_status_map[
                payment_status
            ],
            field_maps[environment]["transaction_paid_date"]: today_date,
        }
    )


def get_knack_refund_payload(
    environment,
    payment_status,
    payment_amount,
    knack_invoice,
    today_date,
    knack_record_id,
):
    """
    :param environment: "uat" or "prod" depending on which endpoint calls this function
    :param payment_status: info from citybase payload
    :param payment_amount: string amount from citybase payload
    :param knack_invoice: info from citybase payload
    :param today_date: mm/dd/YYYY H:M datetime string
    :param knack_record_id:
    :return: json object to insert into transactions table in knack
    """
    refund_fields = {
        "uat": {
            "customer_name": "field_3334",
            "event_name": "field_3348",
            "type": "field_3337",
            "banner_reservations_lpb": "field_3326",
            "banner_reservations_ots": "field_3327",
            "sub_description": "field_3349"
        },
        "prod": {
            "customer_name": "field_3334",
            "event_name": "field_3336",
            "type": "field_3333",
            "banner_reservations_lpb": "field_3328",
            "banner_reservations_ots": "field_3329",
            "sub_description": "field_3351"
        },
    }
    record_response = requests.get(
        f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/{knack_record_id}",
        headers=headers[environment],
    )
    record_data = record_response.json()

    # the connection record id is in the format "field_3326": "<span class=\"638e58b31370e500241c3388\">486</span>",
    # using the raw form of the field to get the identifier.
    try:
        lpb_connection_id = record_data[f'{refund_fields[environment]["banner_reservations_lpb"]}_raw'][0]["identifier"]
    except IndexError:
        lpb_connection_id = None

    try:
        ots_connection_id = record_data[f'{refund_fields[environment]["banner_reservations_ots"]}_raw'][0]["identifier"]
    except IndexError:
        ots_connection_id = None

    return json.dumps(
        {
            field_maps[environment]["payment_status"]: payment_status_map[
                payment_status
            ],
            field_maps[environment]["invoice_id"]: knack_invoice,
            # if it is a refund, store negative amount
            field_maps[environment]["total_amount"]: f"-{payment_amount}",
            field_maps[environment]["created_date"]: today_date,
            field_maps[environment]["transaction_paid_date"]: today_date,
            refund_fields[environment]["customer_name"]: record_data[
                refund_fields[environment]["customer_name"]
            ],
            refund_fields[environment]["event_name"]: record_data[
                refund_fields[environment]["event_name"]
            ],
            refund_fields[environment]["type"]: record_data[
                refund_fields[environment]["type"]
            ],
            refund_fields[environment]["banner_reservations_lpb"]: lpb_connection_id,
            refund_fields[environment]["banner_reservations_ots"]: ots_connection_id,
            refund_fields[environment]["sub_description"]:  record_data[
                refund_fields[environment]["sub_description"]
            ],
        }
    )


def create_message_json(
    environment, citybase_id, today_date, knack_invoice, payment_status
):
    """
    :param environment: "uat" or "prod" depending on which endpoint calls this function
    :param citybase_id: citybase transaction id
    :param today_date: mm/dd/YYYY H:M datetime string
    :param knack_invoice: info from citybase payload
    :param payment_status: info from citybase payload
    :return: json object to insert in knack citybase_messages table
    """
    return json.dumps(
        {
            field_maps[environment]["messages_invoice_id"]: knack_invoice,
            field_maps[environment]["messages_connected_invoice"]: knack_invoice,
            field_maps[environment]["messages_created_date"]: today_date,
            field_maps[environment]["messages_status"]: payment_status,
            field_maps[environment]["messages_citybase_id"]: citybase_id,
        }
    )


def update_parent_reservation(environment, knack_record_id, today_date):
    """
    Uses a knack_record_id to look up the transaction in knack, then finds the appropriate connection field
    And sends payload to knack, marking parent reservation payment received status as TRUE
    """
    record_response = requests.get(
        f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/{knack_record_id}",
        headers=headers[environment],
    )
    record_data = record_response.json()
    if record_data[field_maps[environment]["ots_connection_field"]]:
        # get parent record id
        parent_record_response = record_data[
            field_maps[environment]["ots_connection_field"] + "_raw"
        ]
        parent_record_id = parent_record_response[0]["id"]
        ots_payload = json.dumps(
            {
                field_maps[environment]["ots_application_status"]: "Approved",
                field_maps[environment]["ots_paid_status"]: True,
                field_maps[environment]["ots_payment_date"]: today_date,
            }
        )
        parent_update_response = requests.put(
            f"{KNACK_API_URL}{OTS_OBJECT_ID}/records/{parent_record_id}",
            headers=headers[environment],
            data=ots_payload,
        )
        app.logger.info("Parent update response: " + str(parent_update_response))
    if record_data[field_maps[environment]["lpb_connection_field"]]:
        # get parent record id
        parent_record_response = record_data[
            field_maps[environment]["lpb_connection_field"] + "_raw"
        ]
        parent_record_id = parent_record_response[0]["id"]
        lpb_payload = json.dumps(
            {
                field_maps[environment]["lpb_application_status"]: "Approved",
                field_maps[environment]["lpb_paid_status"]: True,
                field_maps[environment]["lpb_payment_date"]: today_date,
            }
        )
        parent_update_response = requests.put(
            f"{KNACK_API_URL}{LPB_OBJECT_ID}/records/{parent_record_id}",
            headers=headers[environment],
            data=lpb_payload,
        )
        app.logger.info("Parent update response: " + str(parent_update_response))


@app.route("/")
def index():
    now = datetime.now().isoformat()
    return f"Austin Transportation Public Works Department Citybase healthcheck {now}"


@app.route("/citybase_postback", methods=["POST"])
def handle_postback():
    today_date = datetime.now().strftime("%m/%d/%Y %H:%M")
    citybase_data = request.get_json()

    knack_record_id = get_knack_record_id(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple, for example ("Missing custom attributes", 400)
    if not isinstance(knack_record_id, str):
        # returns an error message and error code
        return knack_record_id

    knack_invoice = get_knack_invoice(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple
    if not isinstance(knack_invoice, str):
        # returns an error message and error code
        return knack_invoice

    payment_status = citybase_data["data"]["status"]
    payment_amount = citybase_data["data"]["total_amount"]
    citybase_id = citybase_data["data"]["id"]

    message_payload = create_message_json(
        "prod", citybase_id, today_date, knack_invoice, payment_status
    )
    requests.post(
        f"{KNACK_API_URL}{MESSAGES_OBJECT_ID}/records/",
        headers=headers["prod"],
        data=message_payload,
    )

    # if a refund, post a new record to knack transactions table
    if payment_status == "refunded":
        knack_payload = get_knack_refund_payload(
            "prod",
            payment_status,
            payment_amount,
            knack_invoice,
            today_date,
            knack_record_id,
        )
        knack_response = requests.post(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/",
            headers=headers["prod"],
            data=knack_payload,
        )
    # otherwise, update existing record payment status on transactions table
    else:
        knack_payload = get_knack_payload("prod", payment_status, today_date)
        if payment_status == "successful":
            # if this was a successful payment we also need to update reservation record
            update_parent_reservation("prod", knack_record_id, today_date)
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
    today_date = datetime.now().strftime("%m/%d/%Y %H:%M")
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

    # if a refund, post a new record to knack transactions table
    if payment_status == "refunded":
        knack_payload = get_knack_refund_payload(
            "uat",
            payment_status,
            payment_amount,
            knack_invoice,
            today_date,
            knack_record_id,
        )
        knack_response = requests.post(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID_UAT}/records/",
            headers=headers["uat"],
            data=knack_payload,
        )
    # otherwise, update existing record payment status
    else:
        knack_payload = get_knack_payload("uat", payment_status, today_date)
        if payment_status == "successful":
            # if this was a successful payment we need to update reservation record
            update_parent_reservation("uat", knack_record_id, today_date)
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
