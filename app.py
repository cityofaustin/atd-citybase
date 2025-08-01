from datetime import datetime
import logging
from flask import Flask, request
from watchtower import CloudWatchLogHandler
import requests
import json
import os

from utils.field_maps import FIELD_MAPS
from utils.headers import knack_headers

KNACK_API_URL = "https://api.knack.com/v1/objects/"

flask_env = os.getenv("FLASK_ENV", "staging")
knack_env = "PRODUCTION" if flask_env == "production" else "UAT"

STREET_BANNER_MESSAGES_OBJECT_ID = "object_181"
STREET_BANNER_TRANSACTIONS_OBJECT_ID = "object_180"
OTS_OBJECT_ID = "object_164"
LPB_OBJECT_ID = "object_161"

SMART_MOBILITY_MESSAGES_OBJECT_ID = "object_38"
SMART_MOBILITY_TRANSACTIONS_OBJECT_ID = "object_39"


# map citybase payment statuses to knack options
payment_status_map = {
    "successful": "PAID",
    "voided": "VOID",
    "refunded": "REFUND",
}


app = Flask(__name__)

log_handler = CloudWatchLogHandler(
    log_group_name=f"citybase_{flask_env}", log_stream_name="postback_stream"
)
# logging.basicConfig(level=logging.INFO)
# logging.getLogger().addHandler(log_handler)


def unpack_custom_attributes(custom_attributes_list):
    """
    :param custom_attributes_list: list of dicts {"key":"key_name", "object":"value"} from citybase
    :return: dictionary of "keyname":"value" pairs
    """
    custom_attributes = {}
    for a in custom_attributes_list:
        custom_attributes.update({a["key"]: a["value"]})
    return custom_attributes


def get_object_ids(knack_app):
    if knack_app == "STREET_BANNER":
        return STREET_BANNER_MESSAGES_OBJECT_ID, STREET_BANNER_TRANSACTIONS_OBJECT_ID
    if knack_app == "SMART_MOBILITY":
        return SMART_MOBILITY_MESSAGES_OBJECT_ID, SMART_MOBILITY_TRANSACTIONS_OBJECT_ID
    else:
        raise ValueError(f"Incorrect knack app in payload {knack_app}, must be STREET_BANNER or SMART_MOBILITY")


def create_knack_payload(payment_status, today_date, knack_app):
    """
    :param payment_status: info from citybase payload
    :param today_date: mm/dd/YYYY H:M datetime string
    :return: json object to send along with PUT call to knack
    """
    knack_fields = FIELD_MAPS.get(knack_app).get(knack_env).get("TRANSACTIONS")
    return json.dumps(
        {
            knack_fields["payment_status"]: payment_status_map[payment_status],
            knack_fields["transaction_paid_date"]: today_date,
        }
    )


def get_knack_refund_payload(
    payment_status,
    payment_amount,
    knack_invoice,
    today_date,
    knack_record_id,
    headers,
    transactions_object_id,
    knack_app
):
    """
    :param payment_status: info from citybase payload
    :param payment_amount: string amount from citybase payload
    :param knack_invoice: info from citybase payload
    :param today_date: mm/dd/YYYY H:M datetime string
    :param knack_record_id:
    :return: json object to insert into transactions table in knack
    """

    knack_fields = FIELD_MAPS.get(knack_app).get(knack_env).get("TRANSACTION_REFUND")
    knack_fields.update(FIELD_MAPS.get(knack_app).get(knack_env).get("TRANSACTIONS"))
    record_response = requests.get(
        f"{KNACK_API_URL}{transactions_object_id}/records/{knack_record_id}",
        headers=headers,
    )
    record_response.raise_for_status()
    record_data = record_response.json()
    app.logger.info(f"Parent refund record data from knack")
    app.logger.info(record_data)

    # the connection record id is in the format "field_3326": "<span class=\"638e58b31370e500241c3388\">486</span>",
    # using the raw form of the field to get the identifier.
    try:
        lpb_connection_id = record_data[
            f'{knack_fields["banner_reservations_lpb"]}_raw'
        ][0]["identifier"]
    except IndexError:
        lpb_connection_id = None

    try:
        ots_connection_id = record_data[
            f'{knack_fields["banner_reservations_ots"]}_raw'
        ][0]["identifier"]
    except IndexError:
        ots_connection_id = None

    return json.dumps(
        {
            knack_fields["payment_status"]: payment_status_map[payment_status],
            knack_fields["invoice_id"]: knack_invoice,
            # if it is a refund, store negative amount
            knack_fields["total_amount"]: f"-{payment_amount}",
            knack_fields["created_date"]: today_date,
            knack_fields["transaction_paid_date"]: today_date,
            knack_fields["customer_name"]: record_data[knack_fields["customer_name"]],
            knack_fields["event_name"]: record_data[knack_fields["event_name"]],
            knack_fields["type"]: record_data[knack_fields["type"]],
            knack_fields["banner_reservations_lpb"]: lpb_connection_id,
            knack_fields["banner_reservations_ots"]: ots_connection_id,
            knack_fields["sub_description"]: record_data[
                knack_fields["sub_description"]
            ],
        }
    )


def create_message_json(citybase_id, today_date, knack_invoice, payment_status, knack_app):
    """
    :param citybase_id: citybase transaction id
    :param today_date: mm/dd/YYYY H:M datetime string
    :param knack_invoice: info from citybase payload
    :param payment_status: info from citybase payload
    :return: json object to insert in knack citybase_messages table
    """
    knack_fields = FIELD_MAPS.get(knack_app).get(knack_env).get("MESSAGES")

    return json.dumps(
        {
            knack_fields["messages_invoice_id"]: knack_invoice,
            knack_fields["messages_connected_invoice"]: knack_invoice,
            knack_fields["messages_created_date"]: today_date,
            knack_fields["messages_status"]: payment_status,
            knack_fields["messages_citybase_id"]: citybase_id,
        }
    )


def update_parent_reservation(today_date, parent_record_id, banner_type, headers):
    """
    Checks banner_type and updates appropriate parent reservation record in knack
    Sets payment received status as TRUE, application as Approved and payment date as today
    """

    if banner_type == "OVER_THE_STREET":
        knack_fields = FIELD_MAPS.get("STREET_BANNER").get(knack_env).get("OVER_THE_STREET")
        ots_payload = json.dumps(
            {
                knack_fields["ots_application_status"]: "Approved",
                knack_fields["ots_paid_status"]: True,
                knack_fields["ots_payment_date"]: today_date,
            }
        )
        parent_update_response = requests.put(
            f"{KNACK_API_URL}{OTS_OBJECT_ID}/records/{parent_record_id}",
            headers=headers,
            data=ots_payload,
        )
        app.logger.info("Parent update response: " + str(parent_update_response))
    elif banner_type == "LAMPPOST":
        knack_fields = FIELD_MAPS.get("STREET_BANNER").get(knack_env).get("LAMPPOST")
        lpb_payload = json.dumps(
            {
                knack_fields["lpb_application_status"]: "Approved",
                knack_fields["lpb_paid_status"]: True,
                knack_fields["lpb_payment_date"]: today_date,
            }
        )
        parent_update_response = requests.put(
            f"{KNACK_API_URL}{LPB_OBJECT_ID}/records/{parent_record_id}",
            headers=headers,
            data=lpb_payload,
        )
        app.logger.info("Parent update response: " + str(parent_update_response))


@app.route("/")
def index():
    now = datetime.now().isoformat()
    app.logger.info(f"Healthcheck at {now}")
    return f"Austin Transportation Public Works Department Citybase healthcheck {now}"


@app.errorhandler(500)
def internal_server_error(e):
    # Log the error with more context
    app.logger.error(f"Internal Server Error: {e}", exc_info=True)
    return "Internal server error", 500


@app.route("/citybase_postback", methods=["POST"])
def handle_postback():
    today_date = datetime.now().strftime("%m/%d/%Y %H:%M")
    citybase_data = request.get_json()
    # TODO: validate citybase_data
    app.logger.info(f"New POST with payload: ")
    app.logger.info(citybase_data)
    # information from citybase payload
    custom_attributes = unpack_custom_attributes(citybase_data["data"]["custom_attributes"])
    knack_record_id = custom_attributes["knack_record_id"]
    knack_invoice = custom_attributes["invoice_number"]
    knack_app = custom_attributes["knack_app"]
    banner_type = custom_attributes["banner_type"] if knack_app == "STREET_BANNER" else None
    parent_record_id = custom_attributes["parent_record_id"]
    payment_status = citybase_data["data"]["status"]
    payment_amount = citybase_data["data"]["total_amount"]
    citybase_id = citybase_data["data"]["id"]

    headers = knack_headers(knack_app)
    messages_object_id, transactions_object_id = get_object_ids(knack_app)

    # update the messages table
    message_payload = create_message_json(
        citybase_id, today_date, knack_invoice, payment_status, knack_app
    )
    app.logger.info("Updating Knack messages table with payload: ")
    app.logger.info(message_payload)
    r = requests.post(
        f"{KNACK_API_URL}{messages_object_id}/records/",
        headers=headers,
        data=message_payload,
    )
    app.logger.info(f"Response from updating messages table: {r}")
    r.raise_for_status()

    # if a refund, post a new record to knack transactions table
    if payment_status == "refunded":
        app.logger.info("Transaction is refund, creating new transaction record...")
        knack_payload = get_knack_refund_payload(
            payment_status,
            payment_amount,
            knack_invoice,
            today_date,
            knack_record_id,
            headers,
            transactions_object_id,
            knack_app
        )
        knack_response = requests.post(
            f"{KNACK_API_URL}{transactions_object_id}/records/",
            headers=headers,
            data=knack_payload,
        )
        app.logger.info(f"refund update response {knack_response}")
    # otherwise, update existing record payment status on transactions table
    else:
        app.logger.info("Updating existing transaction record...")
        knack_payload = create_knack_payload(payment_status, today_date, knack_app)
        if payment_status == "successful" and knack_app == "STREET_BANNER":
            # if this was a successful payment we also need to update reservation record
            app.logger.info("Updating parent reservation...")
            update_parent_reservation(today_date, parent_record_id, banner_type, headers)
        knack_response = requests.put(
            f"{KNACK_API_URL}{transactions_object_id}/records/{knack_record_id}",
            headers=headers,
            data=knack_payload,
        )
    if knack_response.status_code == 200:
        return "Payment status updated", knack_response.status_code
    # if unsuccessful, return knack's status response as response
    return knack_response.text, knack_response.status_code


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
