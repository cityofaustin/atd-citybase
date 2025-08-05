from datetime import datetime
import logging
from flask import Flask, request
from watchtower import CloudWatchLogHandler
import requests
import json
import os

from utils.field_maps import FIELD_MAPS, REFUND_FIELDS

KNACK_API_URL = "https://api.knack.com/v1/objects/"

flask_env = os.getenv("FLASK_ENV")
if not flask_env:
    raise Exception("Missing defined environment variable")

KNACK_APP_ID = os.getenv("KNACK_APP_ID")
KNACK_API_KEY = os.getenv("KNACK_API_KEY")
TRANSACTIONS_OBJECT_ID = "object_180"
MESSAGES_OBJECT_ID = "object_181"
OTS_OBJECT_ID = "object_164"
LPB_OBJECT_ID = "object_161"


# map citybase payment statuses to knack options
payment_status_map = {
    "successful": "PAID",
    "voided": "VOID",
    "refunded": "REFUND",
}

headers = {
    "X-Knack-Application-Id": KNACK_APP_ID,
    "X-Knack-REST-API-Key": KNACK_API_KEY,
    "Content-Type": "application/json",
}


app = Flask(__name__)

log_handler = CloudWatchLogHandler(
    log_group_name=f"citybase_{flask_env}", log_stream_name="postback_stream"
)
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(log_handler)


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


def get_knack_payload(payment_status, today_date):
    """
    :param payment_status: info from citybase payload
    :param today_date: mm/dd/YYYY H:M datetime string
    :return: json object to send along with PUT call to knack
    """
    return json.dumps(
        {
            FIELD_MAPS["payment_status"]: payment_status_map[payment_status],
            FIELD_MAPS["transaction_paid_date"]: today_date,
        }
    )


def get_knack_refund_payload(
    payment_status,
    payment_amount,
    knack_invoice,
    today_date,
    knack_record_id,
):
    """
    :param payment_status: info from citybase payload
    :param payment_amount: string amount from citybase payload
    :param knack_invoice: info from citybase payload
    :param today_date: mm/dd/YYYY H:M datetime string
    :param knack_record_id:
    :return: json object to insert into transactions table in knack
    """
    record_response = requests.get(
        f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/{knack_record_id}",
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
            f'{REFUND_FIELDS["banner_reservations_lpb"]}_raw'
        ][0]["identifier"]
    except IndexError:
        lpb_connection_id = None

    try:
        ots_connection_id = record_data[
            f'{REFUND_FIELDS["banner_reservations_ots"]}_raw'
        ][0]["identifier"]
    except IndexError:
        ots_connection_id = None

    return json.dumps(
        {
            FIELD_MAPS["payment_status"]: payment_status_map[payment_status],
            FIELD_MAPS["invoice_id"]: knack_invoice,
            # if it is a refund, store negative amount
            FIELD_MAPS["total_amount"]: f"-{payment_amount}",
            FIELD_MAPS["created_date"]: today_date,
            FIELD_MAPS["transaction_paid_date"]: today_date,
            REFUND_FIELDS["customer_name"]: record_data[REFUND_FIELDS["customer_name"]],
            REFUND_FIELDS["event_name"]: record_data[REFUND_FIELDS["event_name"]],
            REFUND_FIELDS["type"]: record_data[REFUND_FIELDS["type"]],
            REFUND_FIELDS["banner_reservations_lpb"]: lpb_connection_id,
            REFUND_FIELDS["banner_reservations_ots"]: ots_connection_id,
            REFUND_FIELDS["sub_description"]: record_data[
                REFUND_FIELDS["sub_description"]
            ],
        }
    )


def create_message_json(citybase_id, today_date, knack_invoice, payment_status):
    """
    :param citybase_id: citybase transaction id
    :param today_date: mm/dd/YYYY H:M datetime string
    :param knack_invoice: info from citybase payload
    :param payment_status: info from citybase payload
    :return: json object to insert in knack citybase_messages table
    """
    return json.dumps(
        {
            FIELD_MAPS["messages_invoice_id"]: knack_invoice,
            FIELD_MAPS["messages_connected_invoice"]: knack_invoice,
            FIELD_MAPS["messages_created_date"]: today_date,
            FIELD_MAPS["messages_status"]: payment_status,
            FIELD_MAPS["messages_citybase_id"]: citybase_id,
        }
    )


def update_parent_reservation(knack_record_id, today_date):
    """
    Uses a knack_record_id to look up the transaction in knack, then finds the appropriate connection field
    And sends payload to knack, marking parent reservation payment received status as TRUE
    """
    record_response = requests.get(
        f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/{knack_record_id}",
        headers=headers,
    )
    record_data = record_response.json()
    app.logger.info(f"Parent record data from knack")
    app.logger.info(record_data)
    if record_data[FIELD_MAPS["ots_connection_field"]]:
        # get parent record id
        parent_record_response = record_data[
            FIELD_MAPS["ots_connection_field"] + "_raw"
        ]
        parent_record_id = parent_record_response[0]["id"]
        ots_payload = json.dumps(
            {
                FIELD_MAPS["ots_application_status"]: "Approved",
                FIELD_MAPS["ots_paid_status"]: True,
                FIELD_MAPS["ots_payment_date"]: today_date,
            }
        )
        parent_update_response = requests.put(
            f"{KNACK_API_URL}{OTS_OBJECT_ID}/records/{parent_record_id}",
            headers=headers,
            data=ots_payload,
        )
        app.logger.info("Parent update response: " + str(parent_update_response))
    if record_data[FIELD_MAPS["lpb_connection_field"]]:
        # get parent record id
        parent_record_response = record_data[
            FIELD_MAPS["lpb_connection_field"] + "_raw"
        ]
        parent_record_id = parent_record_response[0]["id"]
        lpb_payload = json.dumps(
            {
                FIELD_MAPS["lpb_application_status"]: "Approved",
                FIELD_MAPS["lpb_paid_status"]: True,
                FIELD_MAPS["lpb_payment_date"]: today_date,
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
    app.logger.info(f"New POST with payload: ")
    app.logger.info(citybase_data)
    knack_record_id = get_knack_record_id(citybase_data)
    # if knack_record_id is not a string, then it is an error tuple, for example ("Missing custom attributes", 400)
    if not isinstance(knack_record_id, str):
        # returns an error message and error code
        return knack_record_id

    knack_invoice = get_knack_invoice(citybase_data)
    # if knack_invoice is not a string, then it is an error tuple
    if not isinstance(knack_invoice, str):
        # returns an error message and error code
        return knack_invoice

    payment_status = citybase_data["data"]["status"]
    payment_amount = citybase_data["data"]["total_amount"]
    citybase_id = citybase_data["data"]["id"]
    app.logger.info(f"Payment status: {payment_status}, invoice number: {knack_invoice}")

    message_payload = create_message_json(
        citybase_id, today_date, knack_invoice, payment_status
    )
    app.logger.info("Updating Knack messages table with payload: ")
    app.logger.info(message_payload)
    r = requests.post(
        f"{KNACK_API_URL}{MESSAGES_OBJECT_ID}/records/",
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
        )
        knack_response = requests.post(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/",
            headers=headers,
            data=knack_payload,
        )
        app.logger.info(f"refund update response {knack_response}")
    # otherwise, update existing record payment status on transactions table
    else:
        app.logger.info("Updating existing transaction record...")
        knack_payload = get_knack_payload(payment_status, today_date)
        if payment_status == "successful":
            # if this was a successful payment we also need to update reservation record
            app.logger.info("Updating parent reservation...")
            update_parent_reservation(knack_record_id, today_date)
        knack_response = requests.put(
            f"{KNACK_API_URL}{TRANSACTIONS_OBJECT_ID}/records/{knack_record_id}",
            headers=headers,
            data=knack_payload,
        )
    if knack_response.status_code == 200:
        return "Payment status updated", knack_response.status_code
    # if unsuccessful, return knack's status response as response
    return knack_response.text, knack_response.status_code


if __name__ == "__main__":
    use_debug = flask_env == "development"
    app.run(debug=use_debug, host="0.0.0.0")
