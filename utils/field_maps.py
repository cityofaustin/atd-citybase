FIELD_MAPS = {
    "STREET_BANNER": {
        "PRODUCTION": {
            "TRANSACTION_REFUND": {
                "total_amount": "field_3342",
                "invoice_id": "field_3327",
                "created_date": "field_3320",
                "customer_name": "field_3334",
                "event_name": "field_3336",
                "type": "field_3333",
                "banner_reservations_lpb": "field_3328",
                "banner_reservations_ots": "field_3329",
                "sub_description": "field_3351",
            },
            "MESSAGES": {
                "messages_invoice_id": "field_3363",
                "messages_connected_invoice": "field_3369",  # invoice_transaction
                "messages_created_date": "field_3366",
                "messages_status": "field_3361",
                "messages_citybase_id": "field_3368",
            },
            "TRANSACTIONS": {
                "transaction_status": "field_3353",
                "transaction_paid_date": "field_3352",
            },
            "OVER_THE_STREET": {
                "ots_application_status": "field_2862",
                "ots_payment_received": "field_2858",
                "ots_payment_date": "field_3144",
            },
            "LAMPPOST": {
                "lpb_application_status": "field_2796",
                "lpb_payment_received": "field_2808",
                "lpb_payment_date": "field_2809",
            },
        },
        "UAT": {
            "TRANSACTION_REFUND": {
                "total_amount": "field_3338",
                "invoice_id": "field_3333",
                "created_date": "field_3320",
                "customer_name": "field_3334",
                "event_name": "field_3348",
                "type": "field_3337",
                "banner_reservations_lpb": "field_3326",
                "banner_reservations_ots": "field_3327",
                "sub_description": "field_3349",
            },
            "MESSAGES": {
                "messages_invoice_id": "field_3365",
                "messages_connected_invoice": "field_3372",  # invoice_transactions_banner
                "messages_created_date": "field_3369",
                "messages_status": "field_3367",
                "messages_citybase_id": "field_3378",
            },
            "TRANSACTIONS": {
                "transaction_status": "field_3352",
                "transaction_paid_date": "field_3366",
            },
            "OVER_THE_STREET": {
                "ots_application_status": "field_2862",
                "ots_payment_received": "field_2858",
                "ots_payment_date": "field_3144",
            },
            "LAMPPOST": {
                "lpb_application_status": "field_2796",
                "lpb_payment_received": "field_2808",
                "lpb_payment_date": "field_2809",
            },
        },
    },
    "SMART_MOBILITY": {
        "PRODUCTION": {
            "TRANSACTION_REFUND": {
                "total_amount": "field_833",
                "invoice_id": "field_814",
                "created_date": "field_804",
                "customer_name": "field_817",
                "event_name": "field_818",
                # "type": None,  #not in smart mobility's table
                "sub_description": "field_819",
            },
            "MESSAGES": {
                "messages_invoice_id": "field_795",
                "messages_connected_invoice": "field_825",
                "messages_created_date": "field_799",
                "messages_status": "field_797",
                "messages_citybase_id": "field_801",
            },
            "TRANSACTIONS": {
                "transaction_status": "field_826",
                "transaction_paid_date": "field_827",
            },
        },
        "UAT": {
            "TRANSACTION_REFUND": {
                "total_amount": "field_833",
                "invoice_id": "field_814",
                "created_date": "field_804",
                "customer_name": "field_817",
                "event_name": "field_818",
                # "type": None,  #not in smart mobility's table
                "sub_description": "field_819",
            },
            "MESSAGES": {
                "messages_invoice_id": "field_795",
                "messages_connected_invoice": "field_825",
                "messages_created_date": "field_799",
                "messages_status": "field_797",
                "messages_citybase_id": "field_801",
            },
            "TRANSACTIONS": {
                "transaction_status": "field_826",
                "transaction_paid_date": "field_827",
            },
        },
    },
}
