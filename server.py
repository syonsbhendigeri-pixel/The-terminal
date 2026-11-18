import base64
from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import math
import os
import urllib.parse
import matplotlib
from matplotlib.animation import PillowWriter
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

matplotlib.use("Agg")
sns.set_theme()

PASSCODE = "mr.jafariisthegoat"

D = 0.5
G = 6.674e-11
M_E = 5.9722e24
R_E = 6.371e6
rho_0 = 1.225
H = 8500

LOCK_SCREEN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>THE TERMINAL // Security Clearance Required</title>
  <style>
    * { box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #f8fafc;
      background:
        radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.16), transparent 45%),
        radial-gradient(circle at 80% 80%, rgba(244, 63, 94, 0.14), transparent 45%),
        linear-gradient(180deg, #020617 0%, #090d16 100%);
      padding: 20px;
    }
    .lock-card {
      width: 100%;
      max-width: 420px;
      background: rgba(15, 23, 42, 0.88);
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 18px;
      padding: 32px 28px;
      text-align: center;
      backdrop-filter: blur(12px);
      box-shadow: 0 20px 45px rgba(0, 0, 0, 0.65);
    }
    .badge {
      display: inline-block;
      padding: 5px 14px;
      border-radius: 999px;
      background: rgba(244, 63, 94, 0.15);
      border: 1px solid #f43f5e;
      color: #f43f5e;
      font-size: 0.75rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      margin-bottom: 14px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 1.9rem;
      letter-spacing: 0.16em;
      background: linear-gradient(90deg, #38bdf8, #e0f2fe, #fb923c);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p {
      color: #94a3b8;
      font-size: 0.9rem;
      margin: 0 0 22px;
    }
    input[type="password"] {
      width: 100%;
      background: #020617;
      border: 1px solid #334155;
      color: #38bdf8;
      font-family: 'Consolas', monospace;
      font-size: 1.05rem;
      padding: 12px 14px;
      border-radius: 10px;
      outline: none;
      text-align: center;
      margin-bottom: 14px;
    }
    input[type="password"]:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }
    button {
      width: 100%;
      padding: 13px;
      border: none;
      border-radius: 10px;
      background: linear-gradient(90deg, #0284c7, #38bdf8);
      color: #020617;
      font-weight: 800;
      font-size: 0.95rem;
      letter-spacing: 0.08em;
      cursor: pointer;
    }
    button:hover { opacity: 0.92; }
    .err {
      margin-top: 14px;
      color: #f43f5e;
      font-size: 0.85rem;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div class="lock-card">
    <div class="badge">🔒 RESTRICTED ACCESS</div>
    <h1>THE TERMINAL</h1>
    <p>Enter mission passcode to unlock the Aerospace Drag Simulator.</p>
    <form method="POST" action="/">
      <input type="hidden" name="action" value="unlock" />
      <input type="password" name="passcode" placeholder="Enter passcode..." required autofocus />
      <button type="submit">UNLOCK TERMINAL</button>
    </form>
    {{LOCK_ERROR}}
  </div>
</body>
</html>
"""


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


def get_field(form_data, key, default):
    vals = form_data.get(key)
    return next(iter(vals)) if vals else default


def render_drop_gif(m, h, A, g_val, vt_val):
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
        (5,), (h,), s=sphere_size, color="#38bdf8", edgecolors="white", zorder=5
    )

    rng = np.random.default_rng(42)
    wind_x = rng.uniform(0.5, 9.5, 18)
    wind_y = rng.uniform(0, h, 18)
    wind = ax.scatter(
        wind_x, wind_y, marker="|", s=80, color="#38bdf8", alpha=0.35
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

    total_frames = 40
    t_total = (vt_val / g_val) * 4.5
    times = np.linspace(0, t_total, total_frames)

    writer = PillowWriter(fps=15)
    with writer.saving(fig, "drop_sim.gif", dpi=100):
        for t in times:
            v_curr = vt_val * math.tanh((g_val * t) / vt_val)
            alt_curr = max(0.0, h * (1 - (t / t_total)))
            g_curr = float(calc_gravity(alt_curr))

            sphere.set_offsets(np.column_stack((5, alt_curr)))
            wind_y = (wind_y + (v_curr / vt_val) * (h * 0.06)) % h
            wind.set_offsets(np.c_[wind_x, wind_y])

            hud.set_text(
                f"ALTITUDE: {alt_curr:7.1f} m\n"
                f"GRAVITY:  {g_curr:7.5f} m/s²\n"
                f"SPEED:    {v_curr:7.2f} m/s"
            )
            if v_curr >= 0.97 * vt_val:
                status.set_text("● TERMINAL VELOCITY (a = 0)")
                status.set_color("#34d399")
            else:
                status.set_text("▼ ACCELERATING...")

            writer.grab_frame()
    plt.close(fig)

    with open("drop_sim.gif", "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def render_seaborn_graphs(m, h, A, g_val, vt_val):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    ax1, ax2, ax3, ax4 = axes.flatten()

    h_vals = np.linspace(250, 5000, 200)
    sns.lineplot(
        x=h_vals, y=calc_terminal_velocity(m, h_vals, A), ax=ax1
    ).set(
        title="Velocity vs. Height",
        xlabel="Height (m)",
        ylabel="Terminal Velocity (m/s)",
    )

    A_vals = np.linspace(0.01, 50, 200)
    sns.lineplot(
        x=A_vals, y=calc_terminal_velocity(m, h, A_vals), ax=ax2
    ).set(
        title="Velocity vs. Area",
        xlabel="Cross-Sectional Area (m²)",
        ylabel="Terminal Velocity (m/s)",
    )

    m_vals = np.linspace(0.5, 500, 200)
    sns.lineplot(
        x=m_vals, y=calc_terminal_velocity(m_vals, h, A), ax=ax3
    ).set(
        title="Velocity vs. Mass",
        xlabel="Mass (kg)",
        ylabel="Terminal Velocity (m/s)",
    )

    t_vals = np.linspace(0, (vt_val / g_val) * 4, 200)
    speed_vals = vt_val * np.tanh((g_val * t_vals) / vt_val)
    sns.lineplot(
        x=t_vals, y=speed_vals, ax=ax4, color="darkorange"
    ).set(title="Speed vs. Time", xlabel="Time (s)", ylabel="Speed (m/s)")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=180)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

class TerminalHandler(BaseHTTPRequestHandler):

    def build_lock_page(self, wrong_pass=False):
        err = '<div class="err">❌ ACCESS DENIED: Incorrect Passcode</div>' if wrong_pass else ""
        return LOCK_SCREEN_HTML.replace("{{LOCK_ERROR}}", err).encode("utf-8")

    def build_page(self, form_data=None):
        fields = {"mass": "75", "height": "2000", "area": "0.7"}
        active = "mass"
        show_graphs = False
        said_no = False
        error_html = ""

        if form_data:
            fields["mass"] = get_field(form_data, "mass", "75")
            fields["height"] = get_field(form_data, "height", "2000")
            fields["area"] = get_field(form_data, "area", "0.7")
            active = get_field(form_data, "active_field", "mass")
            show_graphs = get_field(form_data, "show_graphs", "False") == "True"

            key = get_field(form_data, "key", None)
            action = get_field(form_data, "action", None)

            if key:
                fields[active] += key
            elif action == "backspace":
                fields[active] = fields[active][:-1]
            elif action == "clear":
                fields[active] = ""
            elif action == "graphs_yes":
                show_graphs = True
            elif action == "graphs_no":
                show_graphs = False
                said_no = True

        g_str, rho_str, vt_str = "--", "--", "--"
        anim_html = ""
        graphs_html = ""
        no_html = ""

        try:
            m_num = safe_eval(fields["mass"])
            h_num = safe_eval(fields["height"])
            a_num = safe_eval(fields["area"])

            g_val = float(calc_gravity(h_num))
            rho_val = float(calc_density(h_num))
            vt_val = float(calc_terminal_velocity(m_num, h_num, a_num))
            fg_val = m_num * g_val

            g_str = f"{g_val:.5f} m/s² ({fg_val:.1f} N)"
            rho_str = f"{rho_val:.4f} kg/m³"
            vt_str = f"{vt_val:.2f} m/s"

