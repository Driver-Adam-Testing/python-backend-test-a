# Purpose
This code defines two dictionaries, `CONSUMPTION_TIERS` and `SEAT_PRICING_TIERS`, which serve as configuration data for pricing models. The `CONSUMPTION_TIERS` dictionary outlines different consumption plans, each with a range of usage (defined by `min` and `max` values) and an associated price per unit, indicating a tiered pricing structure based on consumption levels. The `SEAT_PRICING_TIERS` dictionary specifies pricing for different seat types, with options for monthly and annual billing, reflecting a subscription-based pricing model. This code provides narrow functionality, primarily serving as a configuration or lookup table for applications that need to calculate costs based on usage or subscription type.
# Global Variables

---
### CONSUMPTION_TIERS 
- **Type**: `dict`
- **Description**: `CONSUMPTION_TIERS` is a dictionary that defines different consumption tiers for a service or product, each with a specified range of usage and corresponding price per unit. The tiers are labeled from 'NO_PLAN' to 'E', with each tier having a 'min' and 'max' value indicating the range of consumption it covers, and a 'price' indicating the cost per unit within that range. This structure allows for scalable pricing based on the level of consumption.
- **Use**: This variable is used to determine the pricing for different levels of consumption based on predefined tiers.


---
### SEAT_PRICING_TIERS 
- **Type**: `dict`
- **Description**: SEAT_PRICING_TIERS is a dictionary that defines pricing tiers for different seat categories in a subscription model. Each key in the dictionary represents a tier name (e.g., 'CORE', 'ADVANCED', 'ENTERPRISE'), and the associated value is another dictionary that specifies the pricing for monthly and/or annual subscriptions. The 'CORE' and 'ADVANCED' tiers have both monthly and annual pricing, while the 'ENTERPRISE' tier only has annual pricing.
- **Use**: This variable is used to determine the cost associated with different subscription tiers based on the selected plan.


