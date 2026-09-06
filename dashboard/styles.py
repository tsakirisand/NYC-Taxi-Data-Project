"""CSS Design System & Theme Configuration for Streamlit Dashboard.

Inspired by Greek Tourism Analytics Project UI/UX architecture.
Clean, corporate blue-slate design system with Inter typography and left-accent cards.
"""

import streamlit as st

# Color Tokens
COLOR_PRIMARY_BLUE = "#005BAE"
COLOR_ACCENT_SKY = "#38BDF8"
COLOR_ACCENT_AMBER = "#F59E0B"
COLOR_SUCCESS_EMERALD = "#10B981"
COLOR_BG_DARK = "#0F172A"
COLOR_CARD_BG = "#1E293B"
COLOR_BORDER = "#334155"


def inject_custom_css():
    """Inject clean corporate CSS theme with Inter typography and metric cards."""
    css_content = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* App Background */
        .stApp {
            background-color: #0F172A;
            color: #F8FAFC;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #1E293B;
            border-right: 1px solid #334155;
        }

        /* Main Header Banner */
        .main-header {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-left: 6px solid #005BAE;
            border-radius: 12px;
            padding: 1.4rem 1.8rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        }

        .main-header-title {
            font-size: 2.0rem;
            font-weight: 800;
            color: #F8FAFC;
            margin: 0;
            letter-spacing: -0.02em;
        }

        .main-header-subtitle {
            font-size: 0.9rem;
            color: #94A3B8;
            margin-top: 0.3rem;
            margin-bottom: 0;
            font-weight: 500;
        }

        /* Metric Cards Grid */
        .metric-card {
            background: #1E293B;
            border: 1px solid #334155;
            border-left: 5px solid #005BAE;
            border-radius: 10px;
            padding: 1rem 1.2rem;
            box-shadow: 0 4px 12px rgba(0, 91, 174, 0.08);
            transition: all 0.2s ease-in-out;
            min-height: 105px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-card:hover {
            transform: translateY(-3px);
            border-color: #0284C7;
            border-left-color: #38BDF8;
            box-shadow: 0 8px 20px rgba(2, 132, 199, 0.2);
            background: #243147;
        }

        .metric-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94A3B8;
            margin-bottom: 0.25rem;
        }

        .metric-value {
            font-size: 1.65rem;
            font-weight: 800;
            color: #38BDF8;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .metric-badge {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            color: #CBD5E1;
            margin-top: 0.35rem;
        }

        /* Streamlit Button Customization */
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid #334155;
            transition: all 0.2s ease;
        }

        /* Tabs customization */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid #334155;
            padding-bottom: 6px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #1E293B;
            border-radius: 8px;
            color: #94A3B8;
            font-weight: 600;
            font-size: 0.88rem;
            border: 1px solid #334155;
            padding: 0 16px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #005BAE !important;
            color: #FFFFFF !important;
            border-color: #38BDF8 !important;
        }
        </style>
    """
    st.markdown(css_content, unsafe_allow_html=True)


def get_plotly_layout_defaults():
    """Return Plotly layout settings for consistent clean slate aesthetic."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94A3B8", size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            gridcolor="#334155",
            zerolinecolor="#475569",
        ),
        yaxis=dict(
            gridcolor="#334155",
            zerolinecolor="#475569",
        ),
    )
