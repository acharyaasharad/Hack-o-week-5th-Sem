"""
Activation Functions Module
===========================
This module provides clean, mathematically sound implementations of four
fundamental activation functions commonly used in neural networks:
    1. Sigmoid Function
    2. ReLU (Rectified Linear Unit)
    3. Tanh (Hyperbolic Tangent)
    4. Binary Step Function

Each function accepts either a single numeric value (int/float) or a NumPy array,
enabling both single-value queries and vectorized computations for plotting.
"""

from typing import Union
import numpy as np


def sigmoid(x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes the Sigmoid activation function.

    Mathematical Formula:
        sigmoid(x) = 1 / (1 + exp(-x))

    Characteristics:
        - Output Range: (0, 1)
        - Behavior: Smooth, S-shaped curve that squashes any real number into
          a probability-like value between 0 and 1.
        - Numerical Stability: Input is clipped to [-500, 500] to prevent
          floating-point overflow in exp(-x) for extreme negative values.

    Args:
        x: Single float/int or NumPy array of inputs.

    Returns:
        float if input is scalar, or NumPy array of outputs.
    """
    x_arr = np.asarray(x, dtype=float)
    # Clip to avoid overflow in exp(-x) when x is strongly negative
    x_safe = np.clip(x_arr, -500.0, 500.0)
    result = 1.0 / (1.0 + np.exp(-x_safe))
    return float(result) if np.isscalar(x) else result


def relu(x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes the Rectified Linear Unit (ReLU) activation function.

    Mathematical Formula:
        ReLU(x) = max(0, x)

    Characteristics:
        - Output Range: [0, +infinity)
        - Behavior:
            - If x < 0: returns 0.0 (deactivates negative inputs).
            - If x >= 0: returns x (identity pass-through for positive inputs).
        - Popularity: Standard default activation for hidden layers in modern
          deep neural networks due to simplicity and computational efficiency.

    Args:
        x: Single float/int or NumPy array of inputs.

    Returns:
        float if input is scalar, or NumPy array of outputs.
    """
    x_arr = np.asarray(x, dtype=float)
    result = np.maximum(0.0, x_arr)
    return float(result) if np.isscalar(x) else result


def tanh(x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes the Hyperbolic Tangent (Tanh) activation function.

    Mathematical Formula:
        tanh(x) = (exp(x) - exp(-x)) / (exp(x) + exp(-x))
                = 2 * sigmoid(2x) - 1

    Characteristics:
        - Output Range: (-1, 1)
        - Behavior: S-shaped curve centered at zero (zero-centered).
            - Strongly negative inputs approach -1.
            - Input of 0 gives exactly 0.
            - Strongly positive inputs approach +1.
        - Advantage over Sigmoid: Zero-centered output makes optimization
          and gradient descent updates faster and more balanced.

    Args:
        x: Single float/int or NumPy array of inputs.

    Returns:
        float if input is scalar, or NumPy array of outputs.
    """
    x_arr = np.asarray(x, dtype=float)
    result = np.tanh(x_arr)
    return float(result) if np.isscalar(x) else result


def step(x: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes the Binary Step (Heaviside) activation function.

    Mathematical Formula:
        step(x) = 0  when x < 0
        step(x) = 1  when x >= 0

    Project Convention:
        In this project, step(0) is explicitly defined as 1.0.

    Characteristics:
        - Output Range: Discrete set {0.0, 1.0}
        - Behavior:
            - Any input strictly less than 0 outputs 0.0.
            - Any input greater than or equal to 0 outputs 1.0.
        - Historical Role: Used in Rosenblatt's classic Perceptron (1958)
          for binary decision making.
        - Limitation: Its derivative is zero everywhere (and undefined at 0),
          making it unsuitable for gradient-based training (backpropagation).

    Args:
        x: Single float/int or NumPy array of inputs.

    Returns:
        float if input is scalar, or NumPy array of outputs.
    """
    x_arr = np.asarray(x, dtype=float)
    result = np.where(x_arr >= 0.0, 1.0, 0.0)
    return float(result) if np.isscalar(x) else result


def get_all_outputs(x: float) -> dict[str, float]:
    """
    Helper function to compute all four activation outputs for a single input value.

    Args:
        x: Single numeric input.

    Returns:
        Dictionary mapping each function name to its calculated output.
    """
    return {
        "Sigmoid": float(sigmoid(x)),
        "ReLU": float(relu(x)),
        "Tanh": float(tanh(x)),
        "Step": float(step(x)),
    }
