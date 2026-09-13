# Paywall Conversion Report

Generated: 2026-09-13T00:59:52+00:00
Window (days): 30

## Funnel
- Views: **68**
- Offer Selects: **6**
- Purchase Attempts: **1**
- Purchase Successes: **0**
- View -> Offer Select: **8.8%**
- Select -> Purchase Attempt: **16.7%**
- Attempt -> Purchase Success: **0.0%**

## Top Failure Reasons
| Reason | Count |
|--------|-------|
| failed | 26 |
| user_cancelled | 1 |

## Failure Breakdown
| Platform | Product ID | Reason | Failures | Users |
|----------|------------|--------|----------|-------|
| android | unknown | failed | 26 | 5 |
| ios | com.iganapolsky.randomtimer.elite | user_cancelled | 1 | 1 |

## Product Funnel
| Platform | Product ID | Selects | Attempts | Successes | Select->Attempt | Attempt->Success |
|----------|------------|---------|----------|-----------|-----------------|------------------|
| ios | com.iganapolsky.randomtimer.elite | 0 | 1 | 0 | 0.0% | 0.0% |
| android | elite_tactical | 6 | 0 | 0 | 0.0% | 0.0% |

## Product Catalog Failures
| Platform | Product ID | Failures | Users |
|----------|------------|----------|-------|
| android | pro_base | 37 | 37 |
| android | elite_tactical | 33 | 33 |
| android | elite_tactical_monthly | 33 | 33 |

## Entry Point Funnel
| Entry Point | Views | Attempts | Successes | View->Attempt | Attempt->Success |
|-------------|-------|----------|-----------|---------------|------------------|
| unknown | 26 | 0 | 0 | 0.0% | 0.0% |
| qualified_training_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| range_gate | 16 | 0 | 0 | 0.0% | 0.0% |
| voice_gate | 6 | 0 | 0 | 0.0% | 0.0% |
| repeat_gate | 4 | 0 | 0 | 0.0% | 0.0% |
| sound_gate | 0 | 1 | 0 | 0.0% | 0.0% |

## Leaky Entry Points
- `unknown` had **26** views and **0** purchase attempts.

## Settings Hotspots
| Setting | Changes | Users |
|---------|---------|-------|
| max_seconds | 3327 | 99 |
| volume | 2099 | 64 |
| min_seconds | 1614 | 98 |
| alarm_duration | 1358 | 95 |
| sound_type | 874 | 87 |
| voice_callouts_enabled | 588 | 46 |
| repeat_enabled | 524 | 89 |
| repeat_rounds | 223 | 44 |
| voice_gender | 212 | 74 |
| vibration_enabled | 178 | 66 |
| use_extended_range | 146 | 47 |
| unknown | 27 | 2 |

## Data Quality Warnings
- unknown paywall entry_point is still receiving meaningful traffic
- product catalog lookup failures detected; verify App Store Connect and Google Play product IDs, approval state, and cleared-for-sale status
