CONSUMPTION_TIERS = {
    "NO_PLAN": {
        "min": 0,
        "max": 0,
        "price": 0.015,
    },
    "A": {
        "min": 0,
        "max": 250000,
        "price": 0.0135,
    },
    "B": {
        "min": 250001,
        "max": 1250000,
        "price": 0.0108,
    },
    "C": {
        "min": 1250001,
        "max": 6250000,
        "price": 0.0086,
    },
    "D": {
        "min": 6250001,
        "max": 31250000,
        "price": 0.0069,
    },
    "E": {
        "min": 31250001,
        "max": 156250000,
        "price": 0.0055,
    },
}

SEAT_PRICING_TIERS = {
    "CORE": {
        "monthly": 40.00,
        "annual": 30.00,
    },
    "ADVANCED": {
        "monthly": 50.00,
        "annual": 40.00,
    },
    "ENTERPRISE": {
        "annual": 50.00,
    },
}
