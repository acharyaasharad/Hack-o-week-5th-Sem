"""
Unit Tests for Activation Functions
===================================
Tests all four activation functions using Python's built-in unittest module.

Required assertions tested:
    - Sigmoid(0) is approximately 0.5
    - ReLU(-5) is 0
    - ReLU(5) is 5
    - Tanh(0) is 0
    - Tanh(5) is close to 1
    - Step(-1) is 0
    - Step(0) is 1 (per project definition)
    - Step(1) is 1
    - All functions work with NumPy arrays
    - Functions return the expected number of outputs for array inputs
"""

import unittest
import numpy as np

from activation_functions import sigmoid, relu, tanh, step, get_all_outputs


class TestActivationFunctions(unittest.TestCase):
    """Test suite verifying mathematical correctness of all activation functions."""

    def test_sigmoid_zero(self):
        """Sigmoid(0) should be approximately 0.5."""
        result = sigmoid(0)
        self.assertAlmostEqual(result, 0.5, places=5)

    def test_sigmoid_extremes(self):
        """Sigmoid of large negative/positive values should be near 0 and 1."""
        self.assertAlmostEqual(sigmoid(-10), 0.0, delta=0.001)
        self.assertAlmostEqual(sigmoid(10), 1.0, delta=0.001)

    def test_relu_negative(self):
        """ReLU(-5) should be 0."""
        result = relu(-5)
        self.assertEqual(result, 0)

    def test_relu_positive(self):
        """ReLU(5) should be 5."""
        result = relu(5)
        self.assertEqual(result, 5)

    def test_relu_zero(self):
        """ReLU(0) should be 0."""
        self.assertEqual(relu(0), 0)

    def test_tanh_zero(self):
        """Tanh(0) should be 0."""
        result = tanh(0)
        self.assertAlmostEqual(result, 0.0, places=5)

    def test_tanh_five(self):
        """Tanh(5) should be close to 1."""
        result = tanh(5)
        self.assertAlmostEqual(result, 1.0, delta=0.01)

    def test_tanh_negative_five(self):
        """Tanh(-5) should be close to -1."""
        result = tanh(-5)
        self.assertAlmostEqual(result, -1.0, delta=0.01)

    def test_step_negative(self):
        """Step(-1) should be 0."""
        result = step(-1)
        self.assertEqual(result, 0)

    def test_step_zero(self):
        """Step(0) should be 1 based on this project's definition."""
        result = step(0)
        self.assertEqual(result, 1)

    def test_step_positive(self):
        """Step(1) should be 1."""
        result = step(1)
        self.assertEqual(result, 1)

    def test_numpy_array_support(self):
        """All functions should accept and return NumPy arrays without error."""
        inputs = np.array([-5.0, -1.0, 0.0, 1.0, 5.0])

        sig_out = sigmoid(inputs)
        rel_out = relu(inputs)
        tnh_out = tanh(inputs)
        stp_out = step(inputs)

        # Check types
        self.assertIsInstance(sig_out, np.ndarray)
        self.assertIsInstance(rel_out, np.ndarray)
        self.assertIsInstance(tnh_out, np.ndarray)
        self.assertIsInstance(stp_out, np.ndarray)

        # Check expected outputs
        np.testing.assert_allclose(sig_out[2], 0.5, atol=1e-5)
        self.assertEqual(rel_out[0], 0.0)
        self.assertEqual(rel_out[4], 5.0)
        self.assertAlmostEqual(tnh_out[2], 0.0, places=5)
        self.assertEqual(stp_out[0], 0.0)
        self.assertEqual(stp_out[2], 1.0)
        self.assertEqual(stp_out[3], 1.0)

    def test_array_output_length(self):
        """Functions should return the exact number of outputs as input elements."""
        n_points = 200
        x_dense = np.linspace(-10, 10, n_points)

        self.assertEqual(len(sigmoid(x_dense)), n_points)
        self.assertEqual(len(relu(x_dense)), n_points)
        self.assertEqual(len(tanh(x_dense)), n_points)
        self.assertEqual(len(step(x_dense)), n_points)

    def test_get_all_outputs_helper(self):
        """Helper get_all_outputs should return correct dictionary structure."""
        outputs = get_all_outputs(0.0)
        self.assertIn("Sigmoid", outputs)
        self.assertIn("ReLU", outputs)
        self.assertIn("Tanh", outputs)
        self.assertIn("Step", outputs)
        self.assertAlmostEqual(outputs["Sigmoid"], 0.5, places=5)
        self.assertEqual(outputs["ReLU"], 0.0)
        self.assertAlmostEqual(outputs["Tanh"], 0.0, places=5)
        self.assertEqual(outputs["Step"], 1.0)


if __name__ == "__main__":
    unittest.main()
