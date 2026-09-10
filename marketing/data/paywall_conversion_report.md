# Paywall Conversion Report

Generated: 2026-09-10T06:34:54+00:00
Window (days): 30

## Funnel
- Views: **71**
- Offer Selects: **6**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **8.5%**
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
| android | pro_base | 28 | 28 |
| android | elite_tactical | 25 | 25 |
| android | elite_tactical_monthly | 25 | 25 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 32 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 17 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 14 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **32** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3489 | 93 |
| volume | 1758 | 55 |
| min_seconds | 1665 | 91 |
| alarm_duration | 1195 | 87 |
| sound_type | 761 | 72 |
| voice_callouts_enabled | 525 | 37 |
| repeat_enabled | 474 | 82 |
| repeat_rounds | 197 | 37 |
| voice_gender | 190 | 65 |
| vibration_enabled | 164 | 63 |
| use_extended_range | 124 | 38 |
| unknown | 36 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
