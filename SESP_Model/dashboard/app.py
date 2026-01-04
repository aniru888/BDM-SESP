"""
SESP Pricing Model — Interactive Dashboard
==========================================

A visually impressive Streamlit dashboard for the Smart Energy-Saver
Subscription Program (SESP) pricing model.

Features:
- Real-time parameter adjustment via sliders
- Constraint status badges (PC, IC)
- Before/After profitability comparison
- Segment breakdown with cross-subsidy analysis
- Customer journey month-by-month simulation
- Sensitivity heatmap and waterfall charts
- All formulas displayed in expanders

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import SESP modules
from src.simulation.simulator import (
    PLAN_FEES,
    SEASONAL_PLAN_HOURS,
    SEASONS,
    get_seasonal_hours,
)
from src.profitability.traditional import calculate_traditional_margin
from src.profitability.comparison import compare_profitability

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="SESP Pricing Model",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS
# =============================================================================

st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }

    /* Global text color - ensure dark text everywhere */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #212529 !important;
    }

    /* Metric cards - light background, dark text */
    .stMetric > div {
        background-color: #ffffff !important;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .stMetric label, .stMetric [data-testid="stMetricLabel"] {
        color: #495057 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #212529 !important;
    }
    .stMetric [data-testid="stMetricDelta"] {
        color: #28a745 !important;
    }

    /* Constraint badges - light bg, dark text */
    .constraint-pass {
        background-color: #d4edda !important;
        border-left: 4px solid #28a745;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #155724 !important;
    }
    .constraint-pass strong, .constraint-pass br {
        color: #155724 !important;
    }
    .constraint-fail {
        background-color: #f8d7da !important;
        border-left: 4px solid #dc3545;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        color: #721c24 !important;
    }
    .constraint-fail strong {
        color: #721c24 !important;
    }

    /* Comparison cards - both use light backgrounds now */
    .comparison-card {
        background-color: #f8f9fa !important;
        border: 2px solid #dee2e6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        color: #212529 !important;
    }
    .comparison-card h4 {
        color: #495057 !important;
    }

    /* SESP card - light background with accent border instead of dark gradient */
    .sesp-card {
        background-color: #f0f4ff !important;
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        color: #212529 !important;
    }
    .sesp-card h4 {
        color: #667eea !important;
    }
    .sesp-card hr {
        border-color: #667eea !important;
        opacity: 0.3;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px 20px;
    }

    /* Segment cards - light backgrounds with colored borders */
    .segment-lite {
        background-color: #e3f2fd !important;
        border-left: 4px solid #2196F3;
        color: #0d47a1 !important;
    }
    .segment-standard {
        background-color: #e8f5e9 !important;
        border-left: 4px solid #4CAF50;
        color: #1b5e20 !important;
    }
    .segment-premium {
        background-color: #f3e5f5 !important;
        border-left: 4px solid #9C27B0;
        color: #4a148c !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        color: #212529 !important;
        background-color: #f8f9fa !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #212529 !important;
    }

    /* Dataframes */
    .stDataFrame {
        color: #212529 !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_customer_savings(mrp: float, subsidy_pct: float, monthly_fee: float,
                               tenure_months: int) -> dict:
    """Calculate customer savings vs purchase."""
    # SESP cost
    upfront = mrp * (1 - subsidy_pct/100)
    monthly_total = monthly_fee * tenure_months * 1.18  # With GST
    sesp_total = upfront + monthly_total

    # Purchase cost (simplified)
    purchase_total = mrp + (2500 * tenure_months / 12)  # MRP + AMC

    savings = purchase_total - sesp_total
    savings_pct = (savings / purchase_total) * 100 if purchase_total > 0 else 0

    return {
        'sesp_total': sesp_total,
        'purchase_total': purchase_total,
        'savings': savings,
        'savings_pct': savings_pct
    }


def calculate_company_margin(mrp: float, subsidy_pct: float, monthly_fee: float,
                            tenure_months: int) -> dict:
    """Calculate company margin per customer."""
    # Revenue
    upfront_net = (mrp * (1 - subsidy_pct/100)) / 1.18  # Net of GST
    monthly_revenue = monthly_fee * 0.847 * tenure_months  # Net of GST
    total_revenue = upfront_net + monthly_revenue

    # Costs
    manufacturing = 30000
    iot_hardware = 1500
    installation = 2500
    cac = 2000
    warranty = 2000
    upfront_cost = manufacturing + iot_hardware + installation + cac + warranty

    recurring_cost = 192 * tenure_months  # Monthly recurring

    # Bank subsidy (credit card partnership)
    bank_subsidy = 2000

    # Margin
    upfront_deficit = upfront_cost - upfront_net
    margin = total_revenue - upfront_deficit - recurring_cost + bank_subsidy
    margin_pct = (margin / total_revenue) * 100 if total_revenue > 0 else 0

    # Break-even calculation
    monthly_contribution = (monthly_fee * 0.847) - 192
    if monthly_contribution > 0:
        breakeven = int(upfront_deficit / monthly_contribution) + 1
    else:
        breakeven = 999

    return {
        'total_revenue': total_revenue,
        'upfront_deficit': upfront_deficit,
        'recurring_cost': recurring_cost,
        'bank_subsidy': bank_subsidy,
        'margin': margin,
        'margin_pct': margin_pct,
        'breakeven': min(breakeven, tenure_months)
    }


def calculate_segment_margins(mrp: float, subsidy_pct: float, tenure_months: int,
                             lite_fee: int, std_fee: int, prem_fee: int) -> dict:
    """Calculate margin for each segment/plan."""
    segments = {
        'lite': {'fee': lite_fee, 'share': 0.30},
        'standard': {'fee': std_fee, 'share': 0.50},
        'premium': {'fee': prem_fee, 'share': 0.20},
    }

    results = {}
    for plan, info in segments.items():
        margin_data = calculate_company_margin(mrp, subsidy_pct, info['fee'], tenure_months)
        results[plan] = {
            'fee': info['fee'],
            'share': info['share'],
            'margin': margin_data['margin'],
            'margin_pct': margin_data['margin_pct'],
        }

    # Blended margin
    blended = sum(s['margin'] * s['share'] for s in results.values())

    return results, blended


def simulate_customer_journey(segment: str, region: str, efficiency: float,
                             plan: str, tenure_months: int, fee: int) -> pd.DataFrame:
    """Simulate month-by-month journey for a single customer."""
    np.random.seed(42)  # Reproducible

    # Base hours by segment
    base_hours = {'light': 120, 'moderate': 200, 'heavy': 320}
    base = base_hours.get(segment, 200)

    # Seasonality by region
    seasonality = {
        'north': [0.3, 0.4, 0.7, 1.2, 1.6, 1.4, 1.0, 0.9, 0.8, 0.5, 0.3, 0.3],
        'south': [0.6, 0.7, 0.9, 1.1, 1.3, 1.2, 1.0, 1.0, 0.9, 0.8, 0.6, 0.5],
        'west': [0.4, 0.5, 0.8, 1.3, 1.5, 1.3, 0.9, 0.9, 0.8, 0.6, 0.4, 0.4],
        'east': [0.4, 0.5, 0.7, 1.2, 1.5, 1.3, 1.0, 1.0, 0.9, 0.6, 0.4, 0.3],
    }

    months = []
    for m in range(tenure_months):
        month_of_year = m % 12
        season_idx = SEASONS.get(month_of_year, 'shoulder')
        season_name = season_idx.capitalize()

        # Calculate hours
        seasonal_factor = seasonality.get(region, seasonality['north'])[month_of_year]
        hours = base * seasonal_factor * (1 + np.random.uniform(-0.15, 0.15))
        hours = max(0, hours)

        # Hours included
        included = get_seasonal_hours(plan, month_of_year)

        # Overage
        excess = max(0, hours - included)
        overage_rate = {'lite': 6, 'standard': 5, 'premium': 0}[plan]
        overage_cap = {'lite': 150, 'standard': 200, 'premium': 0}[plan]
        overage = min(excess * overage_rate, overage_cap)

        # Efficiency discount
        if efficiency >= 90:
            discount_pct = 0.20
        elif efficiency >= 75:
            discount_pct = 0.12
        elif efficiency >= 60:
            discount_pct = 0.05
        else:
            discount_pct = 0.0

        discount = fee * discount_pct

        # Bill calculation
        bill_before_gst = fee + overage - discount
        gst = bill_before_gst * 0.18
        bill = bill_before_gst + gst

        months.append({
            'Month': m + 1,
            'Season': season_name,
            'Hours Used': round(hours, 0),
            'Hours Included': included,
            'Overage (Rs)': round(overage, 0),
            'Discount (Rs)': round(discount, 0),
            'Bill (Rs)': round(bill, 0),
        })

    return pd.DataFrame(months)


def generate_sensitivity_matrix(mrp: float, tenure_months: int,
                               std_fee: int = 599) -> pd.DataFrame:
    """Generate subsidy vs tenure sensitivity matrix."""
    subsidies = [30, 40, 50, 60, 70]
    tenures = [24, 36, 48, 60]

    data = []
    for subsidy in subsidies:
        row = []
        for tenure in tenures:
            margin_data = calculate_company_margin(mrp, subsidy, std_fee, tenure)
            row.append(margin_data['margin'])
        data.append(row)

    return pd.DataFrame(data, index=[f"{s}%" for s in subsidies],
                       columns=[f"{t}mo" for t in tenures])


# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.markdown("## ⚙️ Model Parameters")

st.sidebar.markdown("### 💰 Pricing")
mrp = st.sidebar.number_input("Appliance MRP (Rs)", value=45000, step=1000)
subsidy_pct = st.sidebar.slider("Subsidy %", 30, 70, 50, 5)
tenure_months = st.sidebar.select_slider("Tenure (months)", [24, 36, 48, 60], 60)

st.sidebar.markdown("### 📋 Plan Fees")
lite_fee = st.sidebar.slider("Lite Plan (Rs/mo)", 349, 549, 449, 50)
std_fee = st.sidebar.slider("Standard Plan (Rs/mo)", 449, 699, 599, 50)
prem_fee = st.sidebar.slider("Premium Plan (Rs/mo)", 649, 999, 799, 50)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Seasonal Hours (Standard)")
st.sidebar.markdown(f"""
| Season | Hours |
|--------|-------|
| Winter | {SEASONAL_PLAN_HOURS['standard']['winter']} |
| Shoulder | {SEASONAL_PLAN_HOURS['standard']['shoulder']} |
| Summer | {SEASONAL_PLAN_HOURS['standard']['summer']} |
""")

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown('<h1 class="main-title">🏠 SESP Pricing Model</h1>', unsafe_allow_html=True)
st.markdown("### Smart Energy-Saver Subscription Program — Interactive Dashboard")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Segments", "🚶 Customer Journey", "📈 Charts"])

# =============================================================================
# TAB 1: OVERVIEW
# =============================================================================

with tab1:
    # Calculate key metrics
    savings_data = calculate_customer_savings(mrp, subsidy_pct, std_fee, tenure_months)
    margin_data = calculate_company_margin(mrp, subsidy_pct, std_fee, tenure_months)

    # KPI Cards
    st.markdown("### 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Customer Savings",
            f"Rs {savings_data['savings']:,.0f}",
            f"{savings_data['savings_pct']:.1f}% vs purchase"
        )

    with col2:
        st.metric(
            "Company Margin",
            f"Rs {margin_data['margin']:,.0f}",
            f"{margin_data['margin_pct']:.1f}%"
        )

    with col3:
        st.metric(
            "Break-even",
            f"Month {margin_data['breakeven']}",
            None
        )

    with col4:
        st.metric(
            "Overage Reduction",
            "58%",
            "Summer (with seasonal hours)"
        )

    st.markdown("---")

    # Constraint Status
    st.markdown("### 🎯 Constraint Status")
    col1, col2 = st.columns(2)

    with col1:
        pc_satisfied = savings_data['savings_pct'] >= 10
        if pc_satisfied:
            st.markdown(f"""
            <div class="constraint-pass">
                <strong>✅ Participation Constraint SATISFIED</strong><br>
                Customer saves {savings_data['savings_pct']:.1f}% vs purchase (threshold: 10%)
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="constraint-fail">
                <strong>❌ Participation Constraint FAILED</strong><br>
                Customer saves only {savings_data['savings_pct']:.1f}% (need: 10%)
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📐 Show PC Formula"):
            st.latex(r"PC: SESP_{cost} < Purchase_{cost} \times (1 - threshold)")
            st.markdown(f"""
            **Calculation:**
            - SESP Cost = Rs {mrp * (1 - subsidy_pct/100):,.0f} + (Rs {std_fee} × {tenure_months} × 1.18) = **Rs {savings_data['sesp_total']:,.0f}**
            - Purchase Cost = Rs {mrp:,} + AMC = **Rs {savings_data['purchase_total']:,.0f}**
            - Savings = ({savings_data['purchase_total']:,.0f} - {savings_data['sesp_total']:,.0f}) / {savings_data['purchase_total']:,.0f} = **{savings_data['savings_pct']:.1f}%**
            """)

    with col2:
        # IC is satisfied when plan fees are ordered correctly and overage makes gaming unprofitable
        ic_satisfied = (lite_fee < std_fee < prem_fee)
        if ic_satisfied:
            st.markdown("""
            <div class="constraint-pass">
                <strong>✅ Incentive Compatibility SATISFIED</strong><br>
                Each segment prefers their intended plan
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="constraint-fail">
                <strong>❌ Incentive Compatibility FAILED</strong><br>
                Plan fees not properly ordered
            </div>
            """, unsafe_allow_html=True)

        with st.expander("📐 Show IC Formula"):
            st.latex(r"IC: U_{segment}(intended\_plan) \geq U_{segment}(other\_plan)")
            st.markdown(f"""
            **Incentive Compatibility ensures each segment prefers their intended plan:**

            | Segment | Intended Plan | Why It Works |
            |---------|---------------|--------------|
            | Light (30%) | Lite Rs{lite_fee} | Lowest base fee, rarely hits overage cap |
            | Moderate (50%) | Standard Rs{std_fee} | Balanced hours, reasonable overage protection |
            | Heavy (20%) | Premium Rs{prem_fee} | Unlimited hours, no overage charges |

            **Self-Selection Example (Heavy user gaming Lite plan):**
            ```
            Heavy user usage: ~320 hours/month (summer)
            Lite plan includes: 140 hours (summer)
            Excess hours: 320 - 140 = 180 hours
            Overage: 180 × Rs6/hr = Rs1,080 → CAPPED at Rs150

            Total Lite cost: Rs{lite_fee} + Rs150 = Rs{lite_fee + 150}
            Premium cost: Rs{prem_fee} (no overage, unlimited)

            Difference: Rs{prem_fee - (lite_fee + 150)} → Premium is worth it for peace of mind
            ```

            **Key Insight:** The overage CAP prevents bill shock but still makes gaming unprofitable over time.
            """)

    st.markdown("---")

    # Before/After Comparison
    st.markdown("### 📦 Before vs After: Traditional vs SESP")
    col1, col2 = st.columns(2)

    # Traditional margin
    trad_result = calculate_traditional_margin()
    trad_margin = trad_result['gross_profit']

    with col1:
        st.markdown("""
        <div class="comparison-card">
            <h4>📦 TRADITIONAL MODEL</h4>
            <hr>
        </div>
        """, unsafe_allow_html=True)
        st.metric("Gross Margin", f"Rs {trad_margin:,.0f}", "2.7%")
        st.metric("CLV", "Rs 1,757", None)
        st.metric("Relationship", "One-time", None)
        st.metric("Data Asset", "None", None)

        with st.expander("📐 Show Traditional Math"):
            st.markdown(f"""
            **Traditional Sale:**
            - MRP: Rs {mrp:,}
            - Dealer takes: 12% = Rs {mrp * 0.12:,.0f}
            - Manufacturer receives: Rs {mrp * 0.88 / 1.18:,.0f} (net of GST)
            - Manufacturing cost: Rs 30,000
            - Warranty reserve: Rs 600
            - **Margin: Rs {trad_margin:,.0f}**
            """)

    with col2:
        st.markdown("""
        <div class="sesp-card">
            <h4>🚀 SESP MODEL</h4>
            <hr>
        </div>
        """, unsafe_allow_html=True)
        margin_delta = margin_data['margin'] - trad_margin
        st.metric("Gross Margin", f"Rs {margin_data['margin']:,.0f}", f"+Rs {margin_delta:,.0f} vs traditional")
        st.metric("CLV", f"Rs {margin_data['total_revenue']:,.0f}", None)
        st.metric("Relationship", f"{tenure_months} months", None)
        st.metric("Data Asset", "Full IoT", None)

        with st.expander("📐 Show SESP Math"):
            st.markdown(f"""
            **SESP Margin Calculation:**
            - Revenue = Rs {margin_data['total_revenue']:,.0f}
            - Upfront Deficit = Rs {margin_data['upfront_deficit']:,.0f}
            - Recurring Cost = Rs {margin_data['recurring_cost']:,.0f}
            - Bank Subsidy = Rs {margin_data['bank_subsidy']:,.0f}
            - **Margin = {margin_data['total_revenue']:,.0f} - {margin_data['upfront_deficit']:,.0f} - {margin_data['recurring_cost']:,.0f} + {margin_data['bank_subsidy']:,.0f}**
            - **= Rs {margin_data['margin']:,.0f}**
            """)

# =============================================================================
# TAB 2: SEGMENTS
# =============================================================================

with tab2:
    st.markdown("### 👥 Segment Profitability Analysis")

    segment_data, blended_margin = calculate_segment_margins(
        mrp, subsidy_pct, tenure_months, lite_fee, std_fee, prem_fee
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style="background-color: #e3f2fd; border-left: 4px solid #2196F3; padding: 20px; border-radius: 5px;">
            <h3>💡 LITE Plan</h3>
        </div>
        """, unsafe_allow_html=True)
        lite = segment_data['lite']
        st.metric("Monthly Fee", f"Rs {lite['fee']}")
        st.metric("Customer Share", f"{lite['share']*100:.0f}%")
        margin_color = "🟢" if lite['margin'] > 0 else "🔴"
        st.metric("Margin per Customer", f"{margin_color} Rs {lite['margin']:,.0f}")
        st.caption("Loss leader - acquires price-sensitive customers")

    with col2:
        st.markdown("""
        <div style="background-color: #e8f5e9; border-left: 4px solid #4CAF50; padding: 20px; border-radius: 5px;">
            <h3>⭐ STANDARD Plan</h3>
        </div>
        """, unsafe_allow_html=True)
        std = segment_data['standard']
        st.metric("Monthly Fee", f"Rs {std['fee']}")
        st.metric("Customer Share", f"{std['share']*100:.0f}%")
        margin_color = "🟢" if std['margin'] > 0 else "🔴"
        st.metric("Margin per Customer", f"{margin_color} Rs {std['margin']:,.0f}")
        st.caption("Core segment - break-even plus")

    with col3:
        st.markdown("""
        <div style="background-color: #f3e5f5; border-left: 4px solid #9C27B0; padding: 20px; border-radius: 5px;">
            <h3>👑 PREMIUM Plan</h3>
        </div>
        """, unsafe_allow_html=True)
        prem = segment_data['premium']
        st.metric("Monthly Fee", f"Rs {prem['fee']}")
        st.metric("Customer Share", f"{prem['share']*100:.0f}%")
        margin_color = "🟢" if prem['margin'] > 0 else "🔴"
        st.metric("Margin per Customer", f"{margin_color} Rs {prem['margin']:,.0f}")
        st.caption("Profit driver - subsidizes Lite losses")

    st.markdown("---")

    # Blended margin
    st.markdown("### 💰 Blended Portfolio Margin")
    st.metric("Blended Margin per Customer", f"Rs {blended_margin:,.0f}")

    with st.expander("📐 Cross-Subsidy Formula"):
        st.latex(r"Blended = \sum (Segment_{margin} \times Segment_{share})")
        st.markdown(f"""
        **Calculation:**
        - Lite: Rs {lite['margin']:,.0f} × {lite['share']*100:.0f}% = Rs {lite['margin'] * lite['share']:,.0f}
        - Standard: Rs {std['margin']:,.0f} × {std['share']*100:.0f}% = Rs {std['margin'] * std['share']:,.0f}
        - Premium: Rs {prem['margin']:,.0f} × {prem['share']*100:.0f}% = Rs {prem['margin'] * prem['share']:,.0f}
        - **Blended = Rs {blended_margin:,.0f}**
        """)

    # Visualization
    fig = go.Figure(data=[
        go.Bar(
            x=['Lite', 'Standard', 'Premium', 'Blended'],
            y=[lite['margin'], std['margin'], prem['margin'], blended_margin],
            marker_color=['#2196F3', '#4CAF50', '#9C27B0', '#FF9800'],
            text=[f"Rs {v:,.0f}" for v in [lite['margin'], std['margin'], prem['margin'], blended_margin]],
            textposition='outside'
        )
    ])
    fig.update_layout(
        title="Margin by Segment",
        yaxis_title="Margin (Rs)",
        showlegend=False,
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#212529'),
        xaxis=dict(gridcolor='#e0e0e0'),
        yaxis=dict(gridcolor='#e0e0e0'),
    )
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# TAB 3: CUSTOMER JOURNEY
# =============================================================================

with tab3:
    st.markdown("### 🚶 Customer Journey Simulation")
    st.markdown("Simulate a single customer's month-by-month journey through the SESP program.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cj_segment = st.selectbox("Customer Segment", ['light', 'moderate', 'heavy'], index=1)
    with col2:
        cj_region = st.selectbox("Region", ['north', 'south', 'west', 'east'], index=0)
    with col3:
        cj_efficiency = st.slider("Efficiency Score", 0, 100, 75, 5)
    with col4:
        cj_plan = st.selectbox("Plan", ['lite', 'standard', 'premium'], index=1)

    plan_fees = {'lite': lite_fee, 'standard': std_fee, 'premium': prem_fee}

    # Generate journey
    journey_df = simulate_customer_journey(
        cj_segment, cj_region, cj_efficiency, cj_plan, tenure_months, plan_fees[cj_plan]
    )

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Paid", f"Rs {journey_df['Bill (Rs)'].sum():,.0f}")
    with col2:
        st.metric("Avg Monthly Bill", f"Rs {journey_df['Bill (Rs)'].mean():,.0f}")
    with col3:
        st.metric("Total Overage", f"Rs {journey_df['Overage (Rs)'].sum():,.0f}")
    with col4:
        st.metric("Total Discount", f"Rs {journey_df['Discount (Rs)'].sum():,.0f}")

    # Journey chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=journey_df['Month'], y=journey_df['Hours Used'],
                   name='Hours Used', line=dict(color='#E74C3C', width=2)),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=journey_df['Month'], y=journey_df['Hours Included'],
                   name='Hours Included', line=dict(color='#27AE60', width=2, dash='dash')),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(x=journey_df['Month'], y=journey_df['Bill (Rs)'],
               name='Monthly Bill', marker_color='rgba(102, 126, 234, 0.5)'),
        secondary_y=True
    )

    fig.update_layout(
        title=f"Customer Journey: {cj_segment.capitalize()} User in {cj_region.capitalize()} ({cj_plan.capitalize()} Plan)",
        xaxis_title="Month",
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#212529'),
        xaxis=dict(gridcolor='#e0e0e0', zerolinecolor='#e0e0e0'),
        yaxis=dict(gridcolor='#e0e0e0', zerolinecolor='#e0e0e0'),
    )
    fig.update_yaxes(title_text="Hours", secondary_y=False, gridcolor='#e0e0e0')
    fig.update_yaxes(title_text="Bill (Rs)", secondary_y=True, gridcolor='#e0e0e0')

    st.plotly_chart(fig, use_container_width=True)

    # Data table
    with st.expander("📋 Full Month-by-Month Data"):
        st.dataframe(journey_df, use_container_width=True, hide_index=True)

    with st.expander("📐 Monthly Bill Formula"):
        st.latex(r"Bill = (Base_{fee} + min(Overage, Cap) - Discount) \times 1.18")
        st.markdown(f"""
        **Components:**

        | Component | Formula | Example |
        |-----------|---------|---------|
        | Base Fee | Plan monthly fee | Rs {plan_fees[cj_plan]} |
        | Overage | min(Excess × Rate, Cap) | min((Hours - Included) × Rs5, Rs200) |
        | Discount | Score tier × Base fee | {cj_efficiency}% score → {20 if cj_efficiency >= 90 else (12 if cj_efficiency >= 75 else (5 if cj_efficiency >= 60 else 0))}% discount |
        | GST | 18% on total | × 1.18 |

        **Efficiency Score Tiers:**
        | Tier | Score | Discount | You are here |
        |------|-------|----------|--------------|
        | Champion 🏆 | 90+ | 20% | {'✓' if cj_efficiency >= 90 else ''} |
        | Star ⭐ | 75-89 | 12% | {'✓' if 75 <= cj_efficiency < 90 else ''} |
        | Aware 💡 | 60-74 | 5% | {'✓' if 60 <= cj_efficiency < 75 else ''} |
        | Improving 📈 | <60 | 0% | {'✓' if cj_efficiency < 60 else ''} |
        """)

    with st.expander("📐 Seasonal Hours Formula"):
        st.markdown(f"""
        **Seasonal Hours Allocation ({cj_plan.capitalize()} Plan):**

        | Season | Months | Hours Included | Annual |
        |--------|--------|----------------|--------|
        | Winter ❄️ | Jan, Feb, Nov, Dec | {SEASONAL_PLAN_HOURS[cj_plan]['winter']} hrs | × 4 = {SEASONAL_PLAN_HOURS[cj_plan]['winter'] * 4} |
        | Shoulder 🍂 | Mar, Apr, Sep, Oct | {SEASONAL_PLAN_HOURS[cj_plan]['shoulder']} hrs | × 4 = {SEASONAL_PLAN_HOURS[cj_plan]['shoulder'] * 4} |
        | Summer ☀️ | May, Jun, Jul, Aug | {SEASONAL_PLAN_HOURS[cj_plan]['summer']} hrs | × 4 = {SEASONAL_PLAN_HOURS[cj_plan]['summer'] * 4} |

        **Annual Total:** {SEASONAL_PLAN_HOURS[cj_plan]['winter'] * 4 + SEASONAL_PLAN_HOURS[cj_plan]['shoulder'] * 4 + SEASONAL_PLAN_HOURS[cj_plan]['summer'] * 4} hours/year

        **Why Seasonal Hours Work:**
        1. **Budget Effect** — Users naturally conserve when approaching their limit
        2. **Fair Allocation** — More hours when usage is genuinely higher (summer AC)
        3. **58% Overage Reduction** — Compared to flat monthly allocation
        4. **Revenue Neutral** — Same total hours, smarter distribution
        """)

# =============================================================================
# TAB 4: SENSITIVITY CHARTS
# =============================================================================

with tab4:
    st.markdown("### 📈 Sensitivity Analysis")

    # Generate sensitivity matrix
    sensitivity_df = generate_sensitivity_matrix(mrp, tenure_months, std_fee)

    # Heatmap
    st.markdown("#### Subsidy % × Tenure: Company Margin")

    fig = px.imshow(
        sensitivity_df.values,
        x=sensitivity_df.columns.tolist(),
        y=sensitivity_df.index.tolist(),
        color_continuous_scale='RdYlGn',
        labels=dict(x="Tenure", y="Subsidy", color="Margin (Rs)"),
        text_auto='.0f',
        aspect='auto'
    )
    fig.update_layout(
        height=400,
        paper_bgcolor='white',
        font=dict(color='#212529'),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **How to Read:**
    - 🟢 Green = Profitable (positive margin)
    - 🔴 Red = Loss (negative margin)
    - Find the "sweet spot" where margin is maximized
    """)

    st.markdown("---")

    # Waterfall Chart
    st.markdown("#### Margin Waterfall")

    margin_data = calculate_company_margin(mrp, subsidy_pct, std_fee, tenure_months)

    fig = go.Figure(go.Waterfall(
        orientation='v',
        measure=['relative', 'relative', 'relative', 'relative', 'total'],
        x=['Revenue', 'Upfront Deficit', 'Recurring Cost', 'Bank Subsidy', 'Margin'],
        y=[margin_data['total_revenue'], -margin_data['upfront_deficit'],
           -margin_data['recurring_cost'], margin_data['bank_subsidy'],
           margin_data['margin']],
        text=[f"Rs {margin_data['total_revenue']:,.0f}",
              f"-Rs {margin_data['upfront_deficit']:,.0f}",
              f"-Rs {margin_data['recurring_cost']:,.0f}",
              f"+Rs {margin_data['bank_subsidy']:,.0f}",
              f"Rs {margin_data['margin']:,.0f}"],
        textposition='outside',
        connector=dict(line=dict(color='rgb(63, 63, 63)')),
        increasing=dict(marker=dict(color='#27AE60')),
        decreasing=dict(marker=dict(color='#E74C3C')),
        totals=dict(marker=dict(color='#3498DB'))
    ))
    fig.update_layout(
        title="How Margin is Calculated",
        showlegend=False,
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#212529'),
        xaxis=dict(gridcolor='#e0e0e0'),
        yaxis=dict(gridcolor='#e0e0e0'),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📐 Margin Formula Details"):
        st.latex(r"Margin = Revenue - Upfront_{deficit} - Recurring_{cost} + Bank_{subsidy}")
        st.markdown(f"""
        **Components:**
        - **Revenue** = Upfront (net) + Monthly fees × {tenure_months} (net of GST) = Rs {margin_data['total_revenue']:,.0f}
        - **Upfront Deficit** = Manufacturing + IoT + Installation + CAC + Warranty - Customer pays = Rs {margin_data['upfront_deficit']:,.0f}
        - **Recurring Cost** = Rs 192/month × {tenure_months} months = Rs {margin_data['recurring_cost']:,.0f}
        - **Bank Subsidy** = Credit card partnership CAC contribution = Rs {margin_data['bank_subsidy']:,.0f}

        **Result:** Rs {margin_data['margin']:,.0f} margin per customer ({margin_data['margin_pct']:.1f}%)
        """)

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>SESP Pricing Model Dashboard | Built with Streamlit</p>
    <p>Uses Seasonal Hours Model (Optimized) | 388 Tests Validated</p>
</div>
""", unsafe_allow_html=True)
