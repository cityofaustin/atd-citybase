import os

KNACK_STREET_BANNER_APP_ID = os.getenv("KNACK_STREET_BANNER_APP_ID")
KNACK_STREET_BANNER_API_KEY = os.getenv("KNACK_STREET_BANNER_API_KEY")
KNACK_SMART_MOBILITY_APP_ID = os.getenv("KNACK_SMART_MOBILITY_APP_ID")
KNACK_SMART_MOBILITY_API_KEY = os.getenv("KNACK_SMART_MOBILITY_API_KEY")

def knack_headers(knack_app):
    if knack_app == "STREET_BANNER":
        headers = {
            "X-Knack-Application-Id": KNACK_STREET_BANNER_APP_ID,
            "X-Knack-REST-API-Key": KNACK_STREET_BANNER_API_KEY,
            "Content-Type": "application/json",
        }
    elif knack_app == "SMART_MOBILITY":
        headers = {
            "X-Knack-Application-Id": KNACK_SMART_MOBILITY_APP_ID,
            "X-Knack-REST-API-Key": KNACK_SMART_MOBILITY_API_KEY,
            "Content-Type": "application/json",
        }
    return headers
