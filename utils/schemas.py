payment_reporting_schema = {
    "type": "object",
    "properties": {
        "data": {
            "type":"object",
            "properties": {
                "id": {
                    "type":"integer",
                    "description":"The CityBase internal ID of the payment."
                    },
                "voidable": {
                    "type":"boolean",
                    "description":"Indicates whether or not the payment can be voided."
                    },
                "refundable": {
                    "type": "boolean",
                    "description": "Indicates whether or not the payment can be refunded."
                    },
                "total_amount": {
                    "type":"number",
                    "description":"The amount of the payment with service fee."
                    },
                "service_fee": {
                    "type":"number",
                    "description":"The service fee amount."
                    },
                "amount": {
                    "type":"number",
                    "description":"The amount of the payment before service fee."
                    },
                "payment_source_channel": {
                    "type":"string",
                    "description":"Payment channel of the payment. Options include 'web', 'kiosk', and 'cashier'."
                    },
                "status": {
                    "type":"string",
                    "description":"The current status of the payment."
                    },
                "payment_type":{"type":"string","description":"How the payment was made. Options include 'cash', 'check', 'credit_card', and 'token'."},
                "agency":{"type":"string","description":"The name of the agency for which the payment was made."},
                "associated_payments":{
                    "type":"array",
                    "description":"An array containing other records associated with the payment. Ex. a refund record.",
                    "items":{
                        "type":"object",
                        "properties":{
                            "id": {"type":"integer","description":"ID of the associated record."},
                            "status":{"type":"string","description":"Status of the associated record."}
                            }
                        }
                    },
                "credit_card":{
                    "type":"object",
                    "description":'If payment_type is "credit_card" this object will contain card information. It will be null otherwise.',
                    "properties":{
                        "last_four": {
                            "type":"string",
                            "description":"The last four digits of the credit card number."
                        },
                        "card_type": {
                            "type":"string",
                            "description":"The card type. Ex. visa, discover, etc."
                        }
                    }
                },
                "bank_account":{
                    "type":"object",
                    "description":'If payment_type is "check" this object will contain bank account information. It will be null otherwise.',
                    "properties":{
                        "routing_number": {
                            "type":"string",
                            "description":"The bank account routing number."
                        },
                        "bank_account_type": {
                            "type":"string",
                            "description":"The bank account type. Ex. checking"
                        },
                        "account_number_last_four": {
                            "type":"string",
                            "description":"The last four digits of the bank account number."
                        }
                    }
                },
                created_at:{"type":"string","description":"When the payment was made. Timestamps are in UTC in ISO-8601 format."},
                line_items:{"type":"array","description":"An Array of Line Items.",items:{"type":"object","properties":{id:{type:"string","description":"The ID of the Line Item. Ex. The ID of a Permit being paid for."},amount:{"type":"integer","description":"The Line Item amount."},
                custom_attributes:{"type":"object","description":"An object containing additional information not handled by other fields."}}}},required:["id","amount","custom_attributes"], required:["id","voidable","refundable","status","amount","total_amount","service_fee","total","payment_type","agency","credit_card","bank_account","line_items","created_at","custom_attributes"]}},required:["data"]}}