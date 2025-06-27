# atd-citybase

Healthcheck url, must be on city network: https://citybase.austinmobility.io/

## Description

Flask based endpoint used to accept events delivered by Citybase to the Knack platform and reply to Citybase.

## Integration

Citybase is the payment provider for the Over the Street and Lamppost Banner invoices.
Once a reservation is created and approved in the Knack app, an invoice is generated and marked as ready to pay. Custom [javascript](https://github.com/cityofaustin/atd-knack/blob/master/code/street-banner/street-banner.js#L417) creates a payload to send to the [Citybase endpoint](https://invoice-service.prod.cityba.se/invoices/austin_tx_transportation/street_banner). This request responds with a url to process the payment request. Note, the amount must be in pennies.

Once a user has completed the payment transaction, Citybase sends a postback and waits for us to confirm receipt. Citybase does not consider the payment complete until it receives a 200 response from us.

Example citybase payload
```json
  {
  "data": {
    "total_amount": 6000.00,
    "service_fee": 0.55,
    "amount": 6000.0,
    "voidable": true,
    "refundable": false,
    "id": 70022195,
    "payment_source_channel": "web",
    "status": "refunded",
    "request_id": "not used",
    "payment_type": "credit_card",
    "agency": "Austin Transportation",
    "credit_card": {
      "last_four": "1111",
      "card_type": "visa"
    },
    "bank_account": null,
    "created_at": "2022-10-13T17:58:00Z",
    "line_items": [
      {
        "id": "deea9dae-0121-49dc-be59-c3b40dccdb3d",
        "amount": 600000,
        "custom_attributes": {
          "invoice_number": "INV2022-100250",
          "knack_record_id": "638e5bd41370e500241c3e1f",
          "line_item_description": "Lamppost my big winter event",
          "line_item_sub_description": "INV2022-100250 - convention center"
        }
      }
    ],
    "associated_payments": [],
    "custom_attributes": [
      {
        "key": "invoice_number",
        "value": "INV2022-100250"
      },
      {
        "key": "knack_record_id",
        "value": "638e5bd41370e500241c3e1f"
      }
    ]
  }
}
```

The app first inserts a record in the citybase_messages table in the Street Banners Knack app.
It then updates the transactions table, either by updating the status of the existing transaction or in the case of a refund, inserting a new record.

If the transaction is PAID, then the parent reservation is also updated in knack. 

The response from the transaction update is then sent back to citybase. 

## Development

In the root of the git repository, please:
* `docker-compose build` will build the task environment
* Edit `environment_variables.env` to contain the desired environment variables. See `environment_variables.env_template` for a template
* `docker-compose up -d` should start the app
* Edit files in place outside of the docker instance as usual when developing
