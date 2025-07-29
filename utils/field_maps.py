# map knack field ids to human rememberable names
FIELD_MAPS = {
    "total_amount": "field_3342",
    "payment_status": "field_3353",
    "invoice_id": "field_3327",
    "created_date": "field_3320",
    "transaction_paid_date": "field_3352",
    "messages_invoice_id": "field_3363", # is this different in staging?
    "messages_connected_invoice": "field_3369",
    "messages_created_date": "field_3366",
    "messages_status": "field_3361",
    "messages_citybase_id": "field_3368",
    "ots_connection_field": "field_3329",
    "ots_application_status": "field_2862",  # in banner_reservations object
    "ots_paid_status": "field_2858",  # in banner_reservations object THIS IS CALLED PAYMENT RECEIVED
    "ots_payment_date": "field_3144",  # in banner_reservations object
    "lpb_connection_field": "field_3328",
    "lpb_application_status": "field_2796",  # in banner_reservations object
    "lpb_paid_status": "field_2808",  # in banner_reservations object
    "lpb_payment_date": "field_2809",  # in banner_reservations object
}

REFUND_FIELDS = {
        "customer_name": "field_3334",
        "event_name": "field_3336",
        "type": "field_3333",
        "banner_reservations_lpb": "field_3328",
        "banner_reservations_ots": "field_3329",
        "sub_description": "field_3351",
}
