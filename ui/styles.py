import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1150px;
        }

        /* Metric cards - dark theme friendly */
        div[data-testid="stMetric"] {
            background: #161b22;
            border: 1px solid #30363d;
            padding: 14px 16px;
            border-radius: 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.25);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div {
            color: #f0f6fc !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-weight: 800;
        }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: #7ee787 !important;
        }

        /* Custom cards */
        .tt-card {
            background: #161b22;
            color: #f0f6fc;
            border: 1px solid #30363d;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 10px 0;
            box-shadow: 0 1px 4px rgba(0,0,0,0.25);
        }
        .tt-danger {
            background: #2d1719;
            color: #f0f6fc;
            border: 1px solid #7d2a32;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 10px 0;
        }
        .tt-success {
            background: #14281d;
            color: #f0f6fc;
            border: 1px solid #2f7d4f;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 10px 0;
        }
        .tt-card strong,
        .tt-danger strong,
        .tt-success strong {
            color: #ffffff !important;
            font-size: 1.02rem;
        }
        .tt-muted {
            color: #c9d1d9 !important;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        .tt-emergency-title {
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            color: #ffffff;
        }
        .tt-big-text {
            font-size: 1.25rem;
            line-height: 1.55;
            color: #f0f6fc;
        }
        .tt-mantra {
            background: #101820;
            color: #ffffff;
            border: 1px solid #3b82f6;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 16px 0;
            font-size: 1.2rem;
            line-height: 1.45;
        }

        /* Info boxes can be too bright in dark mode, soften them slightly */
        div[data-testid="stAlert"] {
            border-radius: 14px;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .tt-emergency-title {
                font-size: 1.65rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
