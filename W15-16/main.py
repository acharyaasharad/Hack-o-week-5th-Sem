"""
Activation Function Visualizer
==============================
Main Entry Point of the Application.

This application visualizes and compares four fundamental activation functions:
    1. Sigmoid Function
    2. Rectified Linear Unit (ReLU)
    3. Hyperbolic Tangent (Tanh)
    4. Binary Step Function

Usage:
    python main.py             # Launches interactive Matplotlib visualizer & subplots
    python main.py --cli       # Runs interactive terminal comparison mode (no GUI needed)
    python main.py --save      # Generates and saves high-resolution figures to screenshots/
    python main.py --input 2.5 # Computes all activation outputs for a specific value
    python main.py --explain   # Displays comprehensive beginner educational guide
"""

import sys
import argparse
from typing import Optional

from activation_functions import get_all_outputs
from visualizer import (
    show_visualizations,
    print_comparison_table,
    terminal_input_loop,
    save_all_figures,
)


def print_banner():
    """Prints a friendly ASCII welcome banner for the college project demonstration."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║               ACTIVATION FUNCTION VISUALIZER (PYTHON & NUMPY)            ║
║                    5th Semester Machine Learning Lab                     ║
╚══════════════════════════════════════════════════════════════════════════╝
    Functions Featured:
      1. Sigmoid     : Squashes inputs into (0, 1) probability range
      2. ReLU        : Zero for negative inputs, linear for positive inputs
      3. Tanh        : Zero-centered curve with output in (-1, 1)
      4. Step        : Binary threshold (outputs 0 if x < 0, else 1)
════════════════════════════════════════════════════════════════════════════
"""
    print(banner)


def print_educational_summary():
    """Prints a concise, beginner-friendly educational summary to the console."""
    summary = """
============================================================================
                     EDUCATIONAL SUMMARY & KEY CONCEPTS
============================================================================
1. WHAT IS AN ACTIVATION FUNCTION?
   An activation function decides whether a neuron in a neural network should
   fire (activate) or not by calculating the weighted sum of inputs and adding
   a bias.

2. WHY DO NEURAL NETWORKS NEED NON-LINEAR ACTIVATION FUNCTIONS?
   Without non-linear activation functions, stacking multiple layers of neurons
   would still produce a simple linear combination of inputs (Linear Algebra:
   W2 * (W1 * x) = (W2 * W1) * x = W_combined * x).
   Non-linear functions allow neural networks to learn complex, non-linear
   relationships and act as Universal Function Approximators.

3. FUNCTION OVERVIEW TABLE:
   -------------------------------------------------------------------------
   Function | Formula               | Output Range | Common Application
   -------------------------------------------------------------------------
   Sigmoid  | 1 / (1 + e^-x)        | (0, 1)       | Binary classification outputs
   ReLU     | max(0, x)             | [0, inf)     | Standard hidden layers
   Tanh     | (e^x - e^-x)/(e^x+e^-x)| (-1, 1)      | Zero-centered hidden layers
   Step     | 0 if x<0 else 1       | {0, 1}       | Perceptrons & binary gates
   -------------------------------------------------------------------------

4. KEY VIVA TAKEAWAYS:
   • Vanishing Gradient: Sigmoid & Tanh saturate at extreme inputs (derivatives -> 0).
   • Dying ReLU: Neurons receiving negative inputs output 0 and have 0 gradient.
   • Step Discontinuity: Derivative is zero almost everywhere; cannot use backprop.
============================================================================
"""
    print(summary)


def interactive_menu():
    """Interactive console menu for students demonstrating to an examiner."""
    while True:
        print("\nMain Menu:")
        print("  [1] Open Interactive Matplotlib Graphs (with Slider)")
        print("  [2] Enter Input Value in Terminal (CLI Mode)")
        print("  [3] Show Educational Explanation & Theory")
        print("  [4] Save Graph Screenshots to screenshots/ folder")
        print("  [5] Exit Application")

        try:
            choice = input("\nSelect an option [1-5]: ").strip()
            if choice == "1":
                show_visualizations(save_figures=False)
            elif choice == "2":
                terminal_input_loop()
            elif choice == "3":
                print_educational_summary()
            elif choice == "4":
                saved = save_all_figures()
                print("\nSuccessfully generated screenshots:")
                for k, v in saved.items():
                    print(f"  • {k}: {v}")
            elif choice in ("5", "q", "exit"):
                print("\nThank you for using the Activation Function Visualizer. Goodbye!\n")
                break
            else:
                print("Invalid option. Please choose a number between 1 and 5.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting application.")
            break


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Activation Function Visualizer: Compare Sigmoid, ReLU, Tanh, and Step functions."
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run terminal comparison mode without opening graphical windows."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Generate and save high-resolution figures to screenshots/ directory and exit."
    )
    parser.add_argument(
        "--input",
        type=float,
        metavar="X",
        help="Compute and display all activation outputs for a specific input value X."
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Display the educational theory explanation and exit."
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Open the interactive text menu."
    )

    args = parser.parse_args()

    print_banner()

    # Case 1: Specific input provided via command line
    if args.input is not None:
        print_comparison_table(args.input)
        return

    # Case 2: Save screenshots and exit
    if args.save:
        saved = save_all_figures()
        print("Screenshots saved successfully:")
        for name, path in saved.items():
            print(f"  • {name}: {path}")
        return

    # Case 3: Educational theory explanation
    if args.explain:
        print_educational_summary()
        return

    # Case 4: Terminal comparison mode
    if args.cli:
        terminal_input_loop()
        return

    # Case 5: Interactive menu explicitly requested
    if args.menu:
        interactive_menu()
        return

    # Default action: Automatically ensure screenshots are saved, then launch visualization
    save_all_figures()
    show_visualizations(save_figures=False)


if __name__ == "__main__":
    main()
