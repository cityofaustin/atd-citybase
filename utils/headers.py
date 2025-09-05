import os

KNACK_APP_KEYS = {
    "STREET_BANNER": {
        "app_id": os.getenv("KNACK_STREET_BANNER_APP_ID"),
        "api_key": os.getenv("KNACK_STREET_BANNER_API_KEY"),
    },
    "SMART_MOBILITY": {
        "app_id": os.getenv("KNACK_SMART_MOBILITY_APP_ID"),
        "api_key": os.getenv("KNACK_SMART_MOBILITY_API_KEY"),
    },
}

def knack_headers(knack_app):
    headers = {
        "X-Knack-Application-Id": KNACK_APP_KEYS.get(knack_app).get("app_id"),
        "X-Knack-REST-API-Key": KNACK_APP_KEYS.get(knack_app).get("api_key"),
        "Content-Type": "application/json",
    }
    return headers
