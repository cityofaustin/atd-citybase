STREET_BANNER_TRANSACTION_REFUND_PRODUCTION = {
    "total_amount": "field_3342",
    "invoice_id": "field_3327",
    "created_date": "field_3320",
    "customer_name": "field_3334",
    "event_name": "field_3336",
    "type": "field_3333",
    "banner_reservations_lpb": "field_3328",
    "banner_reservations_ots": "field_3329",
    "sub_description": "field_3351",
}

STREET_BANNER_TRANSACTION_REFUND_DEVELOPMENT = {
    "total_amount": "field_3338",
    "invoice_id": "field_3333",
    "created_date": "field_3320",
    "customer_name": "field_3334",
    "event_name": "field_3348",
    "type": "field_3337",
    "banner_reservations_lpb": "field_3326",
    "banner_reservations_ots": "field_3327",
    "sub_description": "field_3349",
}

STREET_BANNER_MESSAGES_PRODUCTION = {
    "messages_invoice_id": "field_3363",
    "messages_connected_invoice": "field_3369", # invoice_transaction
    "messages_created_date": "field_3366",
    "messages_status": "field_3361",
    "messages_citybase_id": "field_3368",
}

STREET_BANNER_MESSAGES_DEVELOPMENT = {
    "messages_invoice_id": "field_3333",
    "messages_connected_invoice": "field_3372", # invoice_transactions_banner
    "messages_created_date": "field_3369",
    "messages_status": "field_3367",
    "messages_citybase_id": "field_3378",
}

STREET_BANNER_TRANSACTIONS_PRODUCTION = {
    "payment_status": "field_3353", # called transaction status in knack #TODO: rename to match knack
    "transaction_paid_date": "field_3352",
}

STREET_BANNER_TRANSACTIONS_DEVELOPMENT = {
    "payment_status": "field_3352", # called transaction status in knack #TODO: rename to match knack
    "transaction_paid_date": "field_3366",
}

OVER_THE_STREET_PRODUCTION = {
    "ots_application_status": "field_2862",
    "ots_paid_status": "field_2858",  #  THIS IS CALLED PAYMENT RECEIVED
    "ots_payment_date": "field_3144",
}

OVER_THE_STREET_DEVELOPMENT = {
    "ots_application_status": "field_2862",
    "ots_paid_status": "field_2858",  #  THIS IS CALLED PAYMENT RECEIVED
    "ots_payment_date": "field_3144",
}

LAMPPOST_PRODUCTION = {
    "lpb_application_status": "field_2796",
    "lpb_paid_status": "field_2808",  #  THIS IS CALLED PAYMENT RECEIVED
    "lpb_payment_date": "field_2809",
}

LAMPPOST_DEVELOPMENT = {
    "lpb_application_status": "field_2796",
    "lpb_paid_status": "field_2808",  #  THIS IS CALLED PAYMENT RECEIVED
    "lpb_payment_date": "field_2809",
}


# UAT fields

