# Paywall Conversion Report

Generated: 2026-09-07T12:31:41+00:00
Window (days): 30

## Funnel
- Views: **60**
- Offer Selects: **7**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **11.7%**
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
| android | pro_base | 6 | 6 |
| android | elite_tactical | 5 | 5 |
| android | elite_tactical_monthly | 5 | 5 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 30 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 20 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 2 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **30** views and **0** purchase attempts.
- `qualified_training_gate` had **20** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3089 | 64 |
| volume | 1484 | 27 |
| min_seconds | 1337 | 54 |
| alarm_duration | 264 | 52 |
| sound_type | 206 | 36 |
| repeat_enabled | 147 | 46 |
| voice_callouts_enabled | 83 | 7 |
| voice_gender | 62 | 25 |
| vibration_enabled | 53 | 31 |
| unknown | 36 | 2 |
| repeat_rounds | 35 | 7 |
| use_extended_range | 22 | 8 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
