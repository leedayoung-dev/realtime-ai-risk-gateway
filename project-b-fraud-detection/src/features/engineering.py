"""Feature engineering (B-F-03 ~ B-F-06)."""

from __future__ import annotations

from src.models import UserProfile


def build_features(user: UserProfile) -> dict[str, float | int | str]:
    listings = user.listings
    listing_count = len(listings)

    if listing_count:
        price_devs = [
            abs(item.price - item.category_avg_price) / max(item.category_avg_price, 1.0)
            for item in listings
        ]
        price_deviation = sum(price_devs) / len(price_devs)
        titles = [item.title.strip().lower() for item in listings]
        duplicate_listing_ratio = 1.0 - (len(set(titles)) / len(titles))
    else:
        price_deviation = 0.0
        duplicate_listing_ratio = 0.0

    behavior = user.behavior
    network_degree = len(user.network.connected_users)

    return {
        "user_id": user.user_id,
        "account_age_days": user.account_age_days,
        "transaction_count": user.transaction_count,
        "report_count": user.report_count,
        "listing_frequency": listing_count,
        "price_deviation": round(price_deviation, 4),
        "duplicate_listing_ratio": round(duplicate_listing_ratio, 4),
        "messages_per_5m": behavior.messages_per_5m,
        "listing_burst": behavior.listing_burst,
        "new_users_contacted": behavior.new_users_contacted,
        "external_contact_attempt": behavior.external_contact_attempt,
        "network_degree": network_degree,
    }
