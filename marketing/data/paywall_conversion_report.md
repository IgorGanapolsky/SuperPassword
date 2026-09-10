# Paywall Conversion Report

Generated: 2026-09-10T12:31:00+00:00
Window (days): 30

## Funnel
- Views: **69**
- Offer Selects: **6**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **8.7%**
- Select -> Purchase Attempt: **16.7%**
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
| android | elite_tactical | 6 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 30 | 30 |
| android | elite_tactical | 27 | 27 |
| android | elite_tactical_monthly | 27 | 27 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 30 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 17 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 14 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **30** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3410 | 95 |
| volume | 1774 | 58 |
| min_seconds | 1610 | 94 |
| alarm_duration | 1230 | 90 |
| sound_type | 787 | 76 |
| voice_callouts_enabled | 536 | 40 |
| repeat_enabled | 481 | 84 |
| repeat_rounds | 201 | 39 |
| voice_gender | 192 | 66 |
| vibration_enabled | 167 | 65 |
| use_extended_range | 130 | 41 |
| unknown | 36 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
