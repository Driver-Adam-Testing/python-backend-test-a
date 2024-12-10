from database.db import engine
from database.models_v1 import Plan
from sqlalchemy.orm import Session

"""
Free			$0.0150
A	50,000	250,000	$0.0135
B	250,001	1,250,000	$0.0108
C	1,125,001	6,250,000	$0.0086
D	6,250,001	31,250,000	$0.0069
E	31,250,001	156,250,000	$0.0055
"""

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


def plan_name(freq: str) -> str:
    if freq == "monthly":
        return "Monthly"
    elif freq == "annual":
        return "Annual"
    else:
        raise ValueError("Invalid billing period")


INITIAL_PLAN_PRICE_MODELS = {
    "monthly": {
        "core": {
            "seat_price": SEAT_PRICING_TIERS["CORE"]["monthly"],
            "base_usage_price": CONSUMPTION_TIERS["A"]["price"],
        },
        "advanced": {
            "seat_price": SEAT_PRICING_TIERS["ADVANCED"]["monthly"],
            "base_usage_price": CONSUMPTION_TIERS["A"]["price"],
        },
    },
    "annual": {
        "core": {
            "seat_price": SEAT_PRICING_TIERS["CORE"]["annual"],
            "base_usage_price": CONSUMPTION_TIERS["A"]["price"],
        },
        "advanced": {
            "seat_price": SEAT_PRICING_TIERS["ADVANCED"]["annual"],
            "base_usage_price": CONSUMPTION_TIERS["A"]["price"],
        },
        "enterprise": {
            "seat_price": SEAT_PRICING_TIERS["ENTERPRISE"]["annual"],
            "base_usage_price": CONSUMPTION_TIERS["A"]["price"],
        },
    },
}


def core_plans() -> [Plan]:
    m_usage_price = INITIAL_PLAN_PRICE_MODELS["monthly"]["core"]["base_usage_price"]
    m_seat_price = INITIAL_PLAN_PRICE_MODELS["monthly"]["core"]["seat_price"]
    a_usage_price = INITIAL_PLAN_PRICE_MODELS["annual"]["core"]["base_usage_price"]
    a_seat_price = INITIAL_PLAN_PRICE_MODELS["annual"]["core"]["seat_price"]
    return [
        Plan(
            name="Core Plan (Monthly)",
            description="Core monthly plan for small teams",
            base_usage_price=m_usage_price,
            base_seat_price=m_seat_price,
            billing_period="monthly",
        ),
        Plan(
            name="Core Plan (Annual)",
            description="Core annual plan for small teams",
            base_usage_price=a_usage_price,
            base_seat_price=a_seat_price,
            billing_period="annual",
        ),
    ]


def advanced_plans() -> [Plan]:
    m_usage_price = INITIAL_PLAN_PRICE_MODELS["monthly"]["advanced"]["base_usage_price"]
    m_seat_price = INITIAL_PLAN_PRICE_MODELS["monthly"]["advanced"]["seat_price"]
    a_usage_price = INITIAL_PLAN_PRICE_MODELS["annual"]["advanced"]["base_usage_price"]
    a_seat_price = INITIAL_PLAN_PRICE_MODELS["annual"]["advanced"]["seat_price"]
    return [
        Plan(
            name="Advanced Plan (Monthly)",
            description="Advanced monthly plan for medium teams",
            base_usage_price=m_usage_price,
            base_seat_price=m_seat_price,
            billing_period="monthly",
        ),
        Plan(
            name="Advanced Plan (Annual)",
            description="Advanced annual plan for medium teams",
            base_usage_price=a_usage_price,
            base_seat_price=a_seat_price,
            billing_period="annual",
        ),
    ]


def enterprise_plans() -> [Plan]:
    a_usage_price = INITIAL_PLAN_PRICE_MODELS["annual"]["enterprise"][
        "base_usage_price"
    ]
    a_seat_price = INITIAL_PLAN_PRICE_MODELS["annual"]["enterprise"]["seat_price"]
    return [
        Plan(
            name="Enterprise Plan (Annual)",
            description="Enterprise annual plan for large teams",
            base_usage_price=a_usage_price,
            base_seat_price=a_seat_price,
            billing_period="annual",
        )
    ]


def populate_price_plans() -> None:
    with Session(engine) as session:
        plans = core_plans() + advanced_plans() + enterprise_plans()
        session.add_all(plans)
        session.commit()


if __name__ == "__main__":
    populate_price_plans()
