# Participation Constraint Diagnosis Report

**Date:** 2026-01-04
**Status:** Root Cause Identified, Valid Parameters Found

---

## Executive Summary

All 4 original TOPSIS pricing scenarios violate the participation constraint, meaning SESP is MORE EXPENSIVE than outright purchase in every case. This report identifies why and provides valid parameter combinations.

---

## Problem Statement

| Original Scenario | Subsidy | Plan | Customer Savings |
|-------------------|---------|------|------------------|
| Conservative | 22% | Moderate | **-36.1%** |
| Balanced | 33% | Moderate | **-23.2%** |
| Aggressive | 44% | Moderate | **-10.3%** |
| Premium | 18% | Heavy | **-56.1%** |

**All savings are negative = SESP costs MORE than buying outright.**

---

## Root Cause Analysis

### The Three Cost Drivers Making SESP Expensive

#### 1. Monthly Fee Accumulation (Largest Factor)

| Plan | Monthly Fee + GST | × 36 months | NPV (22% rate) |
|------|-------------------|-------------|----------------|
| Light | Rs674 | Rs24,261 | Rs17,970 |
| Moderate | Rs766 | Rs27,576 | Rs20,426 |
| Heavy | Rs1,061 | Rs38,196 | Rs28,293 |

**Issue:** Even moderate fees compound to large NPV over 3 years.

#### 2. Terminal Value Gap (Second Largest)

| Asset | Terminal Value (Year 3) | PV at 22% | Impact |
|-------|-------------------------|-----------|--------|
| Purchased AC | Rs12,000 | Rs6,608 | Customer KEEPS this value |
| SESP AC | Rs0 | Rs0 | Customer owns NOTHING |

**Issue:** Purchase creates an asset; SESP does not. This Rs6,608 PV gap must be offset.

#### 3. GST Cumulative Effect

| Scenario | GST on Subscription | Impact |
|----------|---------------------|--------|
| Purchase | Rs6,864 (one-time on MRP) | Fixed |
| SESP (Mod, 36m) | Rs6,000+ (on fees) + Rs5,400 (on upfront) | Adds up |

**Issue:** GST compounds on every monthly payment.

---

## Component Breakdown (Aggressive Scenario)

```
PURCHASE ALTERNATIVE                  SESP SUBSCRIPTION
─────────────────────────────────────────────────────────────────
MRP (incl GST):         Rs45,000     Subsidized + GST:   Rs29,736
AMC + Repairs (NPV):    Rs 6,880     Monthly fees (NPV): Rs17,970
Terminal Value (PV):   -Rs 6,608     Terminal Value:     Rs     0
─────────────────────────────────────────────────────────────────
TOTAL NPV:              Rs45,271     TOTAL NPV:          Rs49,952
─────────────────────────────────────────────────────────────────
                        DELTA: SESP costs Rs4,681 MORE (-10.3%)
```

---

## Solution: Valid Pricing Parameters

### Grid Search Results

Searched combinations with subsidy 45-70%, all plans, 24 and 36 month tenures.

**Valid combinations (≥10% savings):**

| Rank | Subsidy | Plan | Tenure | Savings | Notes |
|------|---------|------|--------|---------|-------|
| 1 | 70% | Moderate | 24m | **+26.3%** | Best overall |
| 2 | 70% | Light | 24m | **+22.5%** | Budget-friendly |
| 3 | 70% | Moderate | 36m | **+20.2%** | Long tenure viable |
| 4 | 65% | Moderate | 24m | **+19.9%** | Balanced |
| 5 | 65% | Light | 24m | **+16.1%** | Value option |
| 6 | 70% | Heavy | 24m | **+14.1%** | Premium works |
| 7 | 70% | Light | 36m | **+15.4%** | Long budget |
| 8 | 65% | Moderate | 36m | **+14.3%** | Mid-range long |
| 9 | 60% | Moderate | 24m | **+13.5%** | Minimum viable |

### Minimum Subsidy Requirements

| Plan | Min Subsidy % | Min Subsidy Rs | Tenure |
|------|---------------|----------------|--------|
| Light | 65.4% | Rs29,443 | 36m |
| Moderate | 61.4% | Rs27,615 | 36m |
| Heavy | 70.0% | Rs31,500 | 36m |

For 24-month tenure, requirements are ~5% lower.

---

## Recommended New TOPSIS Scenarios

Based on valid parameters, we propose 4 new scenarios:

### Scenario 1: Value Leader (Replaces Aggressive)
- **Subsidy:** 70% (Rs31,500)
- **Plan:** Light (Rs499/month)
- **Tenure:** 24 months
- **Expected Savings:** 22.5%
- **Target:** Price-conscious, low-usage customers

### Scenario 2: Balanced Optimal (Replaces Balanced)
- **Subsidy:** 65% (Rs29,250)
- **Plan:** Moderate (Rs649/month)
- **Tenure:** 24 months
- **Expected Savings:** 19.9%
- **Target:** Average families, mainstream market

### Scenario 3: Extended Value (Replaces Conservative)
- **Subsidy:** 70% (Rs31,500)
- **Plan:** Moderate (Rs649/month)
- **Tenure:** 36 months
- **Expected Savings:** 20.2%
- **Target:** Long-term commitment, family households

### Scenario 4: Premium Service (Replaces Premium)
- **Subsidy:** 70% (Rs31,500)
- **Plan:** Heavy (Rs899/month)
- **Tenure:** 24 months
- **Expected Savings:** 14.1%
- **Target:** Heavy users, WFH, premium service seekers

---

## Business Implications

### Why Original Scenarios Failed

1. **Subsidy too low:** Max 44% was insufficient
2. **Tenure too long:** 36 months amplifies fee accumulation
3. **Heavy plan fee too high:** Rs899/month compounds rapidly

### What This Means for the Business

1. **High Subsidy Required:** 60-70% of MRP must be subsidized
   - Rs31,500 subsidy on Rs45,000 MRP is substantial
   - Company recovers through recurring fees + service margin

2. **Shorter Tenures Preferred:** 24 months > 36 months
   - Less fee accumulation
   - Faster asset cycling
   - Lower customer commitment barrier

3. **Light/Moderate Plans Work Best:**
   - Heavy plan only viable at 70% subsidy
   - Consider phasing out Heavy for SESP

4. **Service Value is Key:**
   - Pure cost comparison favors purchase
   - SESP value = maintenance + warranty + IoT + convenience
   - Must communicate non-price benefits

---

## Next Steps

1. **Update TOPSIS** with 4 new valid scenarios
2. **Re-run MCDM analysis** with valid parameters
3. **Validate profitability** — can company survive at 70% subsidy?
4. **Complete Phase 3** profitability comparison

---

## Diagnostic Script

Full analysis performed by: `SESP_Model/diagnose_pc.py`

Run with: `python -m SESP_Model.diagnose_pc`
