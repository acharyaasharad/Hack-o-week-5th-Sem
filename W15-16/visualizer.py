"""
Visualizer Module
=================
This module handles all Matplotlib plotting for the Activation Function Visualizer:
    1. Combined Comparison Graph with an interactive Matplotlib Slider.
    2. 2x2 Individual Subplots for each activation function.
    3. Terminal-based table comparison for quick command-line checks.
    4. Export functions to save high-resolution figures to the screenshots folder.
"""

import os
from typing import Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

from activation_functions import sigmoid, relu, tanh, step, get_all_outputs

# Styling constants
COLOR_SIGMOID = "#2563eb"  # Royal Blue
COLOR_RELU = "#dc2626"     # Crimson Red
COLOR_TANH = "#16a34a"     # Emerald Green
COLOR_STEP = "#9333ea"     # Purple
COLOR_MARKER = "#111827"   # Dark Slate

LINE_WIDTH = 2.4
X_RANGE = (-10.0, 10.0)
NUM_POINTS = 600


def get_step_plot_data(x_min: float = -10.0, x_max: float = 10.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates disjoint segment points for the Step function to visually
    represent the step jump discontinuity at x = 0 without an artificial diagonal line.

    Returns:
        (x_neg, y_neg, x_pos, y_pos)
    """
    x_neg = np.linspace(x_min, -1e-6, 300)
    y_neg = np.zeros_like(x_neg)
    x_pos = np.linspace(0.0, x_max, 300)
    y_pos = np.ones_like(x_pos)
    return x_neg, y_neg, x_pos, y_pos


def create_combined_figure(initial_x: float = 0.0) -> Tuple[plt.Figure, plt.Axes, dict]:
    """
    Builds the combined comparison figure containing all four activation functions
    along with an interactive Matplotlib Slider widget to inspect outputs dynamically.

    Args:
        initial_x: Initial slider input value (default: 0.0).

    Returns:
        (fig, ax, interactive_elements)
    """
    fig, ax = plt.subplots(figsize=(11, 7.5))
    fig.subplots_adjust(left=0.10, right=0.92, top=0.88, bottom=0.24)

    # Dense input range for smooth curves
    x = np.linspace(X_RANGE[0], X_RANGE[1], NUM_POINTS)

    # Plot continuous curves
    line_sig, = ax.plot(x, sigmoid(x), label="Sigmoid : 1 / (1 + e⁻ˣ)", color=COLOR_SIGMOID, lw=LINE_WIDTH)
    line_rel, = ax.plot(x, relu(x), label="ReLU : max(0, x)", color=COLOR_RELU, lw=LINE_WIDTH)
    line_tnh, = ax.plot(x, tanh(x), label="Tanh : (eˣ - e⁻ˣ) / (eˣ + e⁻ˣ)", color=COLOR_TANH, lw=LINE_WIDTH)

    # Plot Step function with discontinuity
    x_neg, y_neg, x_pos, y_pos = get_step_plot_data(X_RANGE[0], X_RANGE[1])
    ax.plot(x_neg, y_neg, color=COLOR_STEP, lw=LINE_WIDTH)
    ax.plot(x_pos, y_pos, color=COLOR_STEP, lw=LINE_WIDTH, label="Step : 0 if x < 0 else 1")
    ax.plot([0, 0], [0, 1], color=COLOR_STEP, lw=1.2, linestyle=":")
    ax.scatter([0], [1], color=COLOR_STEP, s=40, zorder=5)  # Solid dot at (0, 1)
    ax.scatter([0], [0], facecolors="white", edgecolors=COLOR_STEP, s=40, zorder=5, lw=1.5)  # Open dot at (0, 0)

    # Reference axes at zero
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.9, alpha=0.7)
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.9, alpha=0.7)

    # Reference asymptotes
    ax.axhline(1.0, color="#64748b", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.axhline(-1.0, color="#64748b", linestyle=":", linewidth=0.8, alpha=0.5)

    # Titles and axis labels
    ax.set_title("Comparison of Activation Functions", fontsize=15, fontweight="bold", pad=12)
    ax.set_xlabel("Input (x)", fontsize=12, fontweight="bold", labelpad=8)
    ax.set_ylabel("Activation Output", fontsize=12, fontweight="bold", labelpad=8)
    ax.set_xlim(-10.2, 10.2)
    ax.set_ylim(-1.6, 10.6)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", framealpha=0.92, fontsize=10)

    # Initial vertical marker line for selected input
    v_line = ax.axvline(initial_x, color=COLOR_MARKER, linestyle="-.", linewidth=1.4, alpha=0.75, label="Selected x")

    # Initial scatter markers for each function output
    scat_sig = ax.scatter([initial_x], [sigmoid(initial_x)], color=COLOR_SIGMOID, s=70, zorder=6, edgecolors="black")
    scat_rel = ax.scatter([initial_x], [relu(initial_x)], color=COLOR_RELU, s=70, zorder=6, edgecolors="black")
    scat_tnh = ax.scatter([initial_x], [tanh(initial_x)], color=COLOR_TANH, s=70, zorder=6, edgecolors="black")
    scat_stp = ax.scatter([initial_x], [step(initial_x)], color=COLOR_STEP, s=70, zorder=6, edgecolors="black")

    # Info card text displaying the calculated values
    outputs = get_all_outputs(initial_x)
    info_text = (
        f"Selected Input: x = {initial_x:+.2f}\n"
        f"Sigmoid: {outputs['Sigmoid']:.4f}  |  ReLU: {outputs['ReLU']:.4f}\n"
        f"Tanh:    {outputs['Tanh']:+.4f}  |  Step: {outputs['Step']:.1f}"
    )
    text_box = ax.text(
        0.98, 0.58, info_text,
        transform=ax.transAxes,
        fontsize=10.5,
        fontfamily="monospace",
        verticalalignment="center",
        horizontalalignment="right",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#f8fafc", edgecolor="#cbd5e1", alpha=0.95)
    )

    # Slider widget positioned at the bottom
    slider_ax = fig.add_axes([0.18, 0.08, 0.55, 0.035], facecolor="#f1f5f9")
    slider = Slider(
        ax=slider_ax,
        label="Select Input (x): ",
        valmin=X_RANGE[0],
        valmax=X_RANGE[1],
        valinit=initial_x,
        valstep=0.1,
        color="#3b82f6"
    )

    # Reset button next to the slider
    reset_ax = fig.add_axes([0.78, 0.075, 0.12, 0.045])
    reset_btn = Button(reset_ax, "Reset (x=0)", color="#e2e8f0", hovercolor="#cbd5e1")

    # Callback when slider value changes
    def update(val: float):
        current_x = float(slider.val)
        out = get_all_outputs(current_x)

        # Update vertical reference line
        v_line.set_xdata([current_x, current_x])

        # Update point markers
        scat_sig.set_offsets([[current_x, out["Sigmoid"]]])
        scat_rel.set_offsets([[current_x, out["ReLU"]]])
        scat_tnh.set_offsets([[current_x, out["Tanh"]]])
        scat_stp.set_offsets([[current_x, out["Step"]]])

        # Update text display
        new_text = (
            f"Selected Input: x = {current_x:+.2f}\n"
            f"Sigmoid: {out['Sigmoid']:.4f}  |  ReLU: {out['ReLU']:.4f}\n"
            f"Tanh:    {out['Tanh']:+.4f}  |  Step: {out['Step']:.1f}"
        )
        text_box.set_text(new_text)
        fig.canvas.draw_idle()

    slider.on_changed(update)

    def reset(event):
        slider.reset()

    reset_btn.on_clicked(reset)

    interactive_elements = {
        "slider": slider,
        "reset_btn": reset_btn,
        "update_fn": update,
        "v_line": v_line,
        "text_box": text_box,
    }

    return fig, ax, interactive_elements


def create_individual_subplots_figure() -> Tuple[plt.Figure, np.ndarray]:
    """
    Builds a 2x2 subplot figure showing each activation function in its own dedicated graph
    with tailored y-axis scales, key points, and formulas.

    Returns:
        (fig, axes)
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle("Individual Activation Functions (2 × 2 View)", fontsize=16, fontweight="bold", y=0.98)

    x = np.linspace(X_RANGE[0], X_RANGE[1], NUM_POINTS)

    # 1. Sigmoid Subplot (Top-Left)
    ax_sig = axes[0, 0]
    ax_sig.plot(x, sigmoid(x), color=COLOR_SIGMOID, lw=LINE_WIDTH, label=r"$\sigma(x) = \frac{1}{1 + e^{-x}}$")
    ax_sig.axhline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_sig.axhline(0.5, color="gray", linestyle=":", lw=0.8, alpha=0.6)
    ax_sig.axhline(1.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_sig.axvline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_sig.scatter([0], [0.5], color=COLOR_SIGMOID, s=45, zorder=5)
    ax_sig.text(0.5, 0.45, "(0, 0.5)", fontsize=9, color=COLOR_SIGMOID, fontweight="bold")
    ax_sig.set_title("1. Sigmoid Function", fontsize=13, fontweight="bold", pad=8)
    ax_sig.set_xlabel("Input (x)", fontsize=10)
    ax_sig.set_ylabel("Activation Output", fontsize=10)
    ax_sig.set_xlim(-10.2, 10.2)
    ax_sig.set_ylim(-0.1, 1.1)
    ax_sig.grid(True, linestyle="--", alpha=0.5)
    ax_sig.legend(loc="upper left", fontsize=10)

    # 2. ReLU Subplot (Top-Right)
    ax_rel = axes[0, 1]
    ax_rel.plot(x, relu(x), color=COLOR_RELU, lw=LINE_WIDTH, label=r"$\mathrm{ReLU}(x) = \max(0, x)$")
    ax_rel.axhline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_rel.axvline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_rel.scatter([0], [0], color=COLOR_RELU, s=45, zorder=5)
    ax_rel.text(0.5, 0.4, "Inflection Point (0, 0)", fontsize=9, color=COLOR_RELU, fontweight="bold")
    ax_rel.set_title("2. ReLU (Rectified Linear Unit)", fontsize=13, fontweight="bold", pad=8)
    ax_rel.set_xlabel("Input (x)", fontsize=10)
    ax_rel.set_ylabel("Activation Output", fontsize=10)
    ax_rel.set_xlim(-10.2, 10.2)
    ax_rel.set_ylim(-1.0, 11.0)
    ax_rel.grid(True, linestyle="--", alpha=0.5)
    ax_rel.legend(loc="upper left", fontsize=10)

    # 3. Tanh Subplot (Bottom-Left)
    ax_tnh = axes[1, 0]
    ax_tnh.plot(x, tanh(x), color=COLOR_TANH, lw=LINE_WIDTH, label=r"$\tanh(x) = \frac{e^x - e^{-x}}{e^x + e^{-x}}$")
    ax_tnh.axhline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_tnh.axhline(1.0, color="gray", linestyle=":", lw=0.8, alpha=0.6)
    ax_tnh.axhline(-1.0, color="gray", linestyle=":", lw=0.8, alpha=0.6)
    ax_tnh.axvline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_tnh.scatter([0], [0], color=COLOR_TANH, s=45, zorder=5)
    ax_tnh.text(0.5, -0.15, "Zero-Centered (0, 0)", fontsize=9, color=COLOR_TANH, fontweight="bold")
    ax_tnh.set_title("3. Tanh (Hyperbolic Tangent)", fontsize=13, fontweight="bold", pad=8)
    ax_tnh.set_xlabel("Input (x)", fontsize=10)
    ax_tnh.set_ylabel("Activation Output", fontsize=10)
    ax_tnh.set_xlim(-10.2, 10.2)
    ax_tnh.set_ylim(-1.2, 1.2)
    ax_tnh.grid(True, linestyle="--", alpha=0.5)
    ax_tnh.legend(loc="upper left", fontsize=10)

    # 4. Step Function Subplot (Bottom-Right)
    ax_stp = axes[1, 1]
    x_neg, y_neg, x_pos, y_pos = get_step_plot_data(X_RANGE[0], X_RANGE[1])
    ax_stp.plot(x_neg, y_neg, color=COLOR_STEP, lw=LINE_WIDTH)
    ax_stp.plot(x_pos, y_pos, color=COLOR_STEP, lw=LINE_WIDTH, label=r"$\mathrm{step}(x) = 1 \text{ if } x \geq 0 \text{ else } 0$")
    ax_stp.plot([0, 0], [0, 1], color=COLOR_STEP, lw=1.2, linestyle=":")
    ax_stp.scatter([0], [1], color=COLOR_STEP, s=45, zorder=5)
    ax_stp.scatter([0], [0], facecolors="white", edgecolors=COLOR_STEP, s=45, zorder=5, lw=1.5)
    ax_stp.text(0.5, 0.88, "step(0) = 1.0", fontsize=9, color=COLOR_STEP, fontweight="bold")
    ax_stp.axhline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_stp.axhline(1.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_stp.axvline(0.0, color="gray", linestyle="--", lw=0.8, alpha=0.6)
    ax_stp.set_title("4. Binary Step Function", fontsize=13, fontweight="bold", pad=8)
    ax_stp.set_xlabel("Input (x)", fontsize=10)
    ax_stp.set_ylabel("Activation Output", fontsize=10)
    ax_stp.set_xlim(-10.2, 10.2)
    ax_stp.set_ylim(-0.25, 1.35)
    ax_stp.grid(True, linestyle="--", alpha=0.5)
    ax_stp.legend(loc="upper left", fontsize=10)

    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    return fig, axes


def print_comparison_table(x_val: float):
    """
    Prints a formatted console table comparing all four activation outputs
    for a given input value.

    Args:
        x_val: Selected numeric input.
    """
    outputs = get_all_outputs(x_val)
    print("\n" + "=" * 55)
    print(f"  ACTIVATION OUTPUT COMPARISON FOR INPUT x = {x_val:+.4f}")
    print("=" * 55)
    print(f"  {'Function':<16} {'Formula':<20} {'Output':>12}")
    print("-" * 55)
    print(f"  {'Sigmoid':<16} {'1 / (1 + e^-x)':<20} {outputs['Sigmoid']:>12.6f}")
    print(f"  {'ReLU':<16} {'max(0, x)':<20} {outputs['ReLU']:>12.6f}")
    print(f"  {'Tanh':<16} {'(e^x - e^-x)/(...)':<20} {outputs['Tanh']:>12.6f}")
    print(f"  {'Step':<16} {'0 if x<0 else 1':<20} {outputs['Step']:>12.1f}")
    print("=" * 55)

    # Educational notes based on sign
    if x_val < 0:
        print("  Notice: Negative input causes ReLU to output 0 and")
        print("  Step to output 0. Sigmoid squashes below 0.5, Tanh below 0.")
    elif x_val == 0:
        print("  Notice: At x = 0, Sigmoid is exactly 0.5, Tanh is 0.0,")
        print("  ReLU is 0.0, and Step is 1.0 (per this project's definition).")
    else:
        print("  Notice: Positive input causes ReLU to scale linearly (y = x).")
        print("  Sigmoid saturates toward 1.0 and Tanh saturates toward 1.0.")
    print("=" * 55 + "\n")


def terminal_input_loop():
    """
    Interactive command-line interface allowing the user to enter
    arbitrary input values and view the calculated outputs.
    Serves as a reliable fallback whenever a GUI window cannot be displayed.
    """
    print("\n--- Terminal Output Comparison Mode ---")
    print("Type any real number between -10 and 10 to see activation outputs.")
    print("Type 'q' or 'exit' to return to the main menu.\n")

    while True:
        try:
            user_input = input("Enter an input value (x): ").strip()
            if user_input.lower() in ("q", "exit", "quit"):
                break
            x_val = float(user_input)
            print_comparison_table(x_val)
        except ValueError:
            print("Invalid input. Please enter a valid number (e.g., -2.5, 0, 3.14).")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting terminal comparison mode.")
            break


def save_all_figures(output_dir: str = "screenshots") -> dict[str, str]:
    """
    Saves high-resolution images of both the combined graph and individual subplots
    to the designated screenshots directory.

    Args:
        output_dir: Target directory path.

    Returns:
        Dictionary of saved file paths.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Combined comparison figure
    fig_comb, _, _ = create_combined_figure(initial_x=0.0)
    comb_path = os.path.join(output_dir, "comparison_graph.png")
    fig_comb.savefig(comb_path, dpi=300, bbox_inches="tight")
    plt.close(fig_comb)

    # 2. Individual subplots figure
    fig_sub, _ = create_individual_subplots_figure()
    sub_path = os.path.join(output_dir, "individual_subplots.png")
    fig_sub.savefig(sub_path, dpi=300, bbox_inches="tight")
    plt.close(fig_sub)

    # 3. Combined comparison with positive input example (for report demonstration)
    fig_demo, _, _ = create_combined_figure(initial_x=2.5)
    demo_path = os.path.join(output_dir, "interactive_demo.png")
    fig_demo.savefig(demo_path, dpi=300, bbox_inches="tight")
    plt.close(fig_demo)

    return {
        "comparison_graph": comb_path,
        "individual_subplots": sub_path,
        "interactive_demo": demo_path,
    }


def show_visualizations(save_figures: bool = False):
    """
    Displays the interactive Matplotlib visualizations.
    Opens both the Combined Comparison window with the Slider and the Individual Subplots window.

    Args:
        save_figures: If True, also exports PNG files to screenshots/.
    """
    if save_figures:
        saved = save_all_figures()
        print(f"Saved figures to:\n  - {saved['comparison_graph']}\n  - {saved['individual_subplots']}")

    print("\nOpening Matplotlib visualization windows...")
    print("  Window 1: Combined Comparison Graph (interactive with Slider widget)")
    print("  Window 2: Individual 2x2 Subplots")
    print("Tip: Drag the slider at the bottom of Window 1 to update output values in real-time!\n")

    # Build figures
    fig_comb, _, _ = create_combined_figure(initial_x=0.0)
    fig_sub, _ = create_individual_subplots_figure()

    try:
        plt.show()
    except Exception as e:
        print(f"Note: Could not open GUI window ({e}).")
        print("Falling back to saving figures and terminal output mode.")
        save_all_figures()
        print_comparison_table(0.0)
