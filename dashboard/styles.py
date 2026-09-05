"""CSS Design System & Theme Configuration for Streamlit Dashboard."""

import streamlit as st

# Color Tokens
COLOR_PRIMARY_AMBER = "#f59e0b"
COLOR_CYAN = "#06b6d4"
COLOR_PURPLE = "#8b5cf6"
COLOR_ROSE = "#ec4899"
COLOR_EMERALD = "#10b981"
COLOR_BG_DARK = "#090d16"
COLOR_CARD_BG = "rgba(18, 24, 38, 0.75)"
COLOR_BORDER = "rgba(255, 255, 255, 0.08)"


def inject_custom_css():
    """Inject modern glassmorphism CSS theme and typography."""
    css_content = """
        <style>
        /* App Background */
        .stApp {
            background-color: #090d16;
            color: #f1f5f9;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #0d1322;
            border-right: 1px solid rgba(255, 255, 255, 0.06);
        }

        /* Main Header Banner */
        .main-header {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%);
            border: 1px solid rgba(245, 158, 11, 0.2);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(12px);
        }

        .main-header-title {
            font-family: 'Outfit', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #f59e0b 0%, #ec4899 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -0.02em;
        }

        .main-header-subtitle {
            font-size: 0.95rem;
            color: #94a3b8;
            margin-top: 0.4rem;
            margin-bottom: 0;
        }

        /* Metric Cards Grid */
        .kpi-card {
            background: rgba(18, 24, 38, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 1rem 1.2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            transition: all 0.25s ease-in-out;
            min-height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .kpi-card:hover {
            transform: translateY(-3px);
            border-color: rgba(245, 158, 11, 0.35);
            box-shadow: 0 8px 25px rgba(245, 158, 11, 0.15);
        }

        .kpi-title {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
            margin-bottom: 0.3rem;
        }

        .kpi-value {
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .kpi-badge {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 600;
            padding: 0.15rem 0.4rem;
            border-radius: 6px;
            margin-top: 0.4rem;
            width: fit-content;
        }

        .badge-amber { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
        .badge-cyan { background: rgba(6, 182, 212, 0.15); color: #06b6d4; }
        .badge-purple { background: rgba(139, 92, 246, 0.15); color: #8b5cf6; }
        .badge-rose { background: rgba(236, 72, 153, 0.15); color: #ec4899; }
        .badge-emerald { background: rgba(16, 185, 129, 0.15); color: #10b981; }

        /* Tabs customization */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: transparent;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .stTabs [data-baseweb="tab"] {
            height: 44px;
            background-color: rgba(18, 24, 38, 0.6);
            border-radius: 10px;
            color: #94a3b8;
            font-weight: 600;
            font-size: 0.9rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 0 20px;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%) !important;
            color: #ffffff !important;
            border: 1px solid rgba(245, 158, 11, 0.5) !important;
        }
        </style>
    """
    st.markdown(css_content, unsafe_allow_html=True)


def get_plotly_layout_defaults():
    """Return Plotly layout settings for consistent dark aesthetic."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.05)",
            zerolinecolor="rgba(255, 255, 255, 0.1)",
        ),
        yaxis=dict(
            gridcolor="rgba(255, 255, 255, 0.05)",
            zerolinecolor="rgba(255, 255, 255, 0.1)",
        ),
    )
