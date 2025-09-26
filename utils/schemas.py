payment_reporting_schema = {
    "type": "object",
    "properties": {
        "data": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "The CityBase internal ID of the payment.",
                },
                "voidable": {
                    "type": "boolean",
                    "description": "Indicates whether or not the payment can be voided.",
                },
                "refundable": {
                    "type": "boolean",
                    "description": "Indicates whether or not the payment can be refunded.",
                },
                "total_amount": {
                    "type": "number",
                    "description": "The amount of the payment with service fee.",
                },
                "service_fee": {
                    "type": "number",
                    "description": "The service fee amount.",
                },
                "amount": {
                    "type": "number",
                    "description": "The amount of the payment before service fee.",
                },
                "payment_source_channel": {
                    "type": "string",
                    "description": "Payment channel of the payment. Options include 'web', 'kiosk', and 'cashier'.",
                },
                "status": {
                    "type": "string",
                    "description": "The current status of the payment.",
                },
                "payment_type": {
                    "type": "string",
                    "description": "How the payment was made. Options include 'cash', 'check', 'credit_card', and 'token'.",
                },
                "agency": {
                    "type": "string",
                    "description": "The name of the agency for which the payment was made.",
                },
                "associated_payments": {
                    "type": "array",
                    "description": "An array containing other records associated with the payment. Example: a refund record.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "ID of the associated record.",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status of the associated record.",
                            },
                        },
                    },
                },
                "created_at": {
                    "type": "string",
                    "description": "When the payment was made. Timestamps are in UTC in ISO-8601 format.",
                },
                "line_items": {
                    "type": "array",
                    "description": "An Array of Line Items.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "The ID of the Line Item. Example: The ID of a Permit being paid for.",
                            },
                            "amount": {
                                "type": "integer",
                                "description": "The Line Item amount.",
                            },
                            "custom_attributes": {
                                "type": "object",
                                "description": "An object containing additional information not handled by other fields.",
                            },
                        },
                    },
                    "required": ["id", "amount", "custom_attributes"],
                },
                "custom_attributes": {
                    "type": "array",
                    "description": "An array containing additional information not handled by other fields.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                            },
                            "value": {
                                "type": "string",
                            },
                        },
                    },
                },
            },
            "required": [
                "id",
                "status",
                "amount",
                "total_amount",
                "service_fee",
                "payment_type",
                "agency",
                "line_items",
                "created_at",
                "custom_attributes",
            ],
        },
    },
    "required": ["data"],
}

custom_attributes_schema = {
    "type": "object",
    "properties": {
        "knack_record_id": {"type": "string"},
        "invoice_number": {"type": "string"},
        "parent_record_id": {"type": "string"},
        "banner_type": {"type": "string", "enum": ["LAMPPOST", "OVER_THE_STREET"]},
        "knack_app": {"type": "string", "enum": ["STREET_BANNER", "SMART_MOBILITY"]},
    },
    "required": ["knack_record_id", "invoice_number", "parent_record_id", "knack_app"],
}
