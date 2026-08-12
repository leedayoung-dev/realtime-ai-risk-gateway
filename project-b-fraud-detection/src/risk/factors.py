"""Risk factor explanation (B-F-10)."""

from __future__ import annotations


def explain_factors(features: dict[str, float | int | str]) -> dict[str, str]:
    factors: dict[str, str] = {}

    if int(features["listing_burst"]) >= 2:
        factors["listing_burst"] = "HIGH"
    if float(features["price_deviation"]) >= 0.4:
        factors["price_anomaly"] = "HIGH"
    if int(features["messages_per_5m"]) >= 15:
        factors["chat_pattern"] = "HIGH"
    elif int(features["messages_per_5m"]) >= 8:
        factors["chat_pattern"] = "MEDIUM"
    if int(features["account_age_days"]) < 7:
        factors["account_age"] = "HIGH"
    elif int(features["account_age_days"]) < 30:
        factors["account_age"] = "MEDIUM"
    if int(features["report_count"]) >= 2:
        factors["report_history"] = "HIGH"
    elif int(features["report_count"]) == 1:
        factors["report_history"] = "MEDIUM"
    if int(features["external_contact_attempt"]) >= 2:
        factors["external_contact"] = "HIGH"
    if float(features["duplicate_listing_ratio"]) >= 0.5:
        factors["duplicate_listing"] = "MEDIUM"

    if not factors:
        factors["baseline"] = "LOW"
    return factors
