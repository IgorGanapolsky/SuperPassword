# Paywall Conversion Report

Generated: 2026-09-08T12:31:32+00:00
Window (days): 30

## Funnel
- Views: **73**
- Offer Selects: **7**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **9.6%**
- Select -> Purchase Attempt: **14.3%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 26 |
| user_cancelled | 2 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 26 | 5 |
| ios | com.iganapolsky.randomtimer.pro | user_cancelled | 2 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.pro | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 7 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 25 | 25 |
| android | elite_tactical | 22 | 22 |
| android | elite_tactical_monthly | 22 | 22 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 34 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 19 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **34** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3259 | 88 |
| volume | 1691 | 49 |
| min_seconds | 1581 | 83 |
| alarm_duration | 980 | 81 |
| sound_type | 635 | 65 |
| voice_callouts_enabled | 435 | 30 |
| repeat_enabled | 416 | 74 |
| repeat_rounds | 163 | 30 |
| voice_gender | 161 | 55 |
| vibration_enabled | 143 | 57 |
| use_extended_range | 103 | 31 |
| unknown | 36 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
