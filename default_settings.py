"""Default preferences used to initialize missing database settings."""

DEFAULT_SETTINGS = {
    "personal_target_hours": 35.0,
    "tier_threshold_minutes": 30.0,
    "bonus_milestones": [
        {"hours": 20.0, "bonus": 43.50},
        {"hours": 35.0, "bonus": 101.50},
    ],
    "extra_earnings": 0.0,
    "use_live_fx": False,
    "usd_mxn_rate": 18.50,
    "conversion_fee_percent": 0,
    "usd_mxn_source": "manual",
    "usd_mxn_last_updated": "",
}
