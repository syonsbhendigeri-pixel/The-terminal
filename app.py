import math
import os
import matplotlib
from matplotlib.animation import PillowWriter
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st

matplotlib.use("Agg")
sns.set_theme()

# 1. Page Setup & Sleek Aerospace Dark Theme
st.set_page_config(page_title="THE TERMINAL", page_icon="🚀", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #0f172a, #020617);
        color: #f8fafc;
    }
    div[data-testid="stMetric"] {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 12px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-family: monospace;
    }
    button[kind="secondary"] {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid rgba(148, 163, 184, 0.25);
        font-weight: bold;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<h1 style='text-align:center; letter-spacing:0.18em; color:#38bdf8;'>THE TERMINAL</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#94a3b8;'>PYTHON AEROSPACE DRAG &amp; TERMINAL VELOCITY CALCULATOR</p>",
    unsafe_allow_html=True,
)

# 2. Physics Constants & Equations from your PDF
D = 0.5
G = 6.674e-11
M_E = 5.9722e24
R_E = 6.371e6
rho_0 = 1.225
H = 8500


def calc_gravity(h):
    return G * (M_E / (R_E + h) ** 2)


def calc_density(h):
    return rho_0 * np.exp(-h / H)


def calc_terminal_velocity(m, h, A):
    return np.sqrt((2 * m * calc_gravity(h)) / (D * calc_density(h) * A))


def safe_eval(expr):
    clean = str(expr).replace("^", "**")
    val = float(
        eval(
            clean,
            {"__builtins__": None},
            {"sqrt": math.sqrt, "pi": math.pi, "exp": math.exp},
        )
    )
    if val <= 0:
        raise ValueError("Must be positive")
    return val


# 3. Calculator Memory
if "mass" not in st.session_state:
    st.session_state.mass = "75"
if "height" not in st.session_state:
    st.session_state.height = "2000"
if "area" not in st.session_state:
    st.session_state.area = "0.7"
if "active" not in st.session_state:
    st.session_state.active = "mass"
if "show_graphs" not in st.session_state:
    st.session_state.show_graphs = None


def press_key(k):
    st.session_state[st.session_state.active] += k


def backspace():
    st.session_state[st.session_state.active] = st.session_state[st.session_state.active][:-1]


def clear_field():
    st.session_state[st.session_state.active] = ""


# 4. Built-in Python Animation Generator (No FFmpeg Needed)
def render_drop_video(m, h, A, g_val, vt_val, filename="drop_sim.gif"):
    fig, ax = plt.subplots(figsize=(7, 3.6), facecolor="#020617")
    ax.set_facecolor("#020617")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, h * 1.12)
    ax.set_ylabel("Altitude (m)", color="#94a3b8", fontsize=9)
    ax.set_xticks([])
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_color("#1e293b")

    ax.axhline(0, color="#34d399", lw=2)
    ax.text(
        0.2,
        h * 0.02,
        "EARTH SURFACE (0 m)",
        color="#34d399",
        fontsize=8,
        fontweight="bold",
    )

    sphere_size = min(450, max(120, 120 + math.sqrt(A) * 90))
    sphere = ax.scatter(
        (5,),
        (h,),
        s=sphere_size,
        color="#38bdf8",
        edgecolors="white",
        zorder=5,
    )

    rng = np.random.default_rng(42)
    wind_x = rng.uniform(0.5, 9.5, 18)
    wind_y = rng.uniform(0, h, 18)
    wind = ax.scatter(
        wind_x,
        wind_y,
        marker="|",
        s=80,
        color="#38bdf8",
        alpha=0.35,
    )

    hud = ax.text(
        0.3,
        h * 0.96,
        "",
        color="#f8fafc",
        fontsize=9,
        family="monospace",
        va="top",
    )
    status = ax.text(
        9.7,
        h * 0.96,
        "",
        color="#fb923c",
        fontsize=9,
        family="monospace",
        fontweight="bold",
        ha="right",
        va="top",
    )

    total_frames = 50
    t_total = (vt_val / g_val) * 4.5
    times = np.linspace(0, t_total, total_frames)

    writer = PillowWriter(fps=15)
    with writer.saving(fig, filename, dpi=100):
        for t in times:
            v_curr = vt_val * math.tanh((g_val * t) / vt_val)
            alt_curr = max(0.0, h * (1 - (t / t_total)))

            sphere.set_offsets(np.column_stack((5, alt_curr)))
            wind_y = (wind_y + (v_curr / vt_val) * (h * 0.06)) % h
            wind.set_offsets(np.c_[wind_x, wind_y])

            hud.set_text(
                f"ALTITUDE: {alt_curr:7.1f} m\n"
                f"SPEED:    {v_curr:7.2f} m/s\n"
                f"GRAVITY:  {g_val:7.4f} m/s²"
            )
            if v_curr >= 0.97 * vt_val:
                status.set_text("● TERMINAL VELOCITY (a = 0)")
                status.set_color("#34d399")
            else:
                status.set_text("▼ ACCELERATING...")

            writer.grab_frame()
    plt.close(fig)


# 5. Interface Layout
left_col, right_col = st.columns((1, 1.5), gap="large")

with left_col:
    st.subheader("🎛️ Scientific Inputs")
    st.session_state.active = st.radio(
        "Select active keypad target:",
        ("mass", "height", "area"),
        format_func=lambda x: {
            "mass": "Mass (kg)",
            "height": "Drop Height (m)",
            "area": "Cross-Sectional Area (m²)",
        }[x],
        horizontal=True,
    )

    st.text_input("Mass (kg)", key="mass")
    st.text_input("Drop Height (m)", key="height")
    st.text_input("Cross-Sectional Area (m²)", key="area")

    keys = (
        (("√", "sqrt("), ("xʸ", "**"), ("×10ˣ", "e"), ("⌫", "BACK")),
        (("7", "7"), ("8", "8"), ("9", "9"), ("÷", "/")),
        (("4", "4"), ("5", "5"), ("6", "6"), ("×", "*")),
        (("1", "1"), ("2", "2"), ("3", "3"), ("−", "-")),
        (("C", "CLEAR"), ("0", "0"), (".", "."), ("+", "+")),
        (("(", "("), (")", ")"), ("π", "pi"), ("=", "COMPUTE")),
    )

    for row in keys:
        cols = st.columns(4)
        for i, (label, val) in enumerate(row):
            if val == "BACK":
                cols[i].button(
                    label,
                    key=f"btn_{label}_{i}",
                    use_container_width=True,
                    on_click=backspace,
                )
            elif val == "CLEAR":
                cols[i].button(
                    label,
                    key=f"btn_{label}_{i}",
                    use_container_width=True,
                    on_click=clear_field,
                )
            elif val == "COMPUTE":
                cols[i].button(
                    label,
                    key=f"btn_{label}_{i}",
                    use_container_width=True,
                    type="primary",
                )
            else:
                cols[i].button(
                    label,
                    key=f"btn_{label}_{i}",
                    use_container_width=True,
                    on_click=press_key,
                    args=(val,),
                )

    launch_btn = st.button(
        "🚀 COMPUTE & RENDER DROP ANIMATION",
        type="primary",
        use_container_width=True,
    )

with right_col:
    try:
        m_num = safe_eval(st.session_state.mass)
        h_num = safe_eval(st.session_state.height)
        a_num = safe_eval(st.session_state.area)

        g_val = float(calc_gravity(h_num))
        rho_val = float(calc_density(h_num))
        vt_val = float(calc_terminal_velocity(m_num, h_num, a_num))

        c1, c2, c3 = st.columns(3)
        c1.metric("Gravity g(h)", f"{g_val:.4f} m/s²")
        c2.metric("Air Density ρ(h)", f"{rho_val:.4f} kg/m³")
        c3.metric("Terminal Velocity (vT)", f"{vt_val:.2f} m/s")

        if launch_btn or not os.path.exists("drop_sim.gif"):
            with st.spinner("Rendering physics drop animation in Python..."):
                render_drop_video(m_num, h_num, a_num, g_val, vt_val)

        if os.path.exists("drop_sim.gif"):
            st.image("drop_sim.gif", use_container_width=True)

        st.markdown("---")
        q_col, yes_col, no_col = st.columns((3, 1, 1))
        q_col.markdown("**Would you like to generate the 4 Seaborn physics graphs?**")
        if yes_col.button("YES", use_container_width=True):
            st.session_state.show_graphs = True
        if no_col.button("NO", use_container_width=True):
            st.session_state.show_graphs = False

        if st.session_state.show_graphs is False:
            st.success("OK, HAVE A GOOD DAY!!!!!")

    except Exception:
        st.error("Enter valid positive math expressions (e.g., 75, sqrt(49), 4.2e-3).")

# 6. Seaborn Graphs Output
if st.session_state.show_graphs is True:
    st.markdown("---")
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax1, ax2, ax3, ax4 = axes.flatten()

    # Graph 1: Velocity vs. Height
    h_vals = np.linspace(250, 5000, 200)
    sns.lineplot(
        x=h_vals,
        y=calc_terminal_velocity(m_num, h_vals, a_num),
        ax=ax1,
    ).set(
        title="Velocity vs. Height",
        xlabel="Height (m)",
        ylabel="Terminal Velocity (m/s)",
    )

    # Graph 2: Velocity vs. Area
    A_vals = np.linspace(0.01, 50, 200)
    sns.lineplot(
        x=A_vals,
        y=calc_terminal_velocity(m_num, h_num, A_vals),
        ax=ax2,
    ).set(
        title="Velocity vs. Area",
        xlabel="Cross-Sectional Area (m²)",
        ylabel="Terminal Velocity (m/s)",
    )

    # Graph 3: Velocity vs. Mass
    m_vals = np.linspace(0.5, 500, 200)
    sns.lineplot(
        x=m_vals,
        y=calc_terminal_velocity(m_vals, h_num, a_num),
        ax=ax3,
    ).set(
        title="Velocity vs. Mass",
        xlabel="Mass (kg)",
        ylabel="Terminal Velocity (m/s)",
    )

    # Graph 4: Speed vs. Time
