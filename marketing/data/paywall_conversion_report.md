# Paywall Conversion Report

Generated: 2026-09-08T20:56:08+00:00
Window (days): 30

## Funnel
- Views: **70**
- Offer Selects: **7**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **10.0%**
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
| unknown | 32 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 18 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 12 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **32** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3309 | 86 |
| volume | 1704 | 49 |
| min_seconds | 1627 | 83 |
| alarm_duration | 986 | 79 |
| sound_type | 633 | 63 |
| voice_callouts_enabled | 435 | 30 |
| repeat_enabled | 419 | 74 |
| repeat_rounds | 163 | 30 |
| voice_gender | 162 | 55 |
| vibration_enabled | 141 | 56 |
| use_extended_range | 103 | 31 |
| unknown | 36 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
