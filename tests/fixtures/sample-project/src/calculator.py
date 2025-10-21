"""
Calculator module for basic arithmetic operations

This module provides a Calculator class with various arithmetic operations.
It follows Python best practices and includes comprehensive documentation.
"""

from typing import List, Union


class Calculator:
    """
    A simple calculator class for performing basic arithmetic operations

    This class implements standard arithmetic operations following
    IEEE 754 floating-point arithmetic standards.
    """

    def __init__(self):
        """Initialize the calculator with default settings"""
        self.memory = 0.0
        self.history = []

    def calculate_total(self, items: List[Union[int, float]]) -> float:
        """
        Calculate the total sum of numeric items

        This is a public API method that computes the sum of all numeric
        values in the provided list.

        Args:
            items: List of numeric values (int or float)

        Returns:
            float: Sum of all items in the list

        Raises:
            TypeError: If items is not a list
            ValueError: If list contains non-numeric values

        Example:
            >>> calc = Calculator()
            >>> calc.calculate_total([1, 2, 3, 4, 5])
            15.0
        """
        if not isinstance(items, list):
            raise TypeError("items must be a list")

        try:
            total = sum(items)
            self.history.append(('total', items, total))
            return float(total)
        except TypeError as e:
            raise ValueError("All items must be numeric") from e

    def add(self, a: float, b: float) -> float:
        """
        Add two numbers

        Args:
            a: First number
            b: Second number

        Returns:
            float: Sum of a and b
        """
        result = a + b
        self.history.append(('add', a, b, result))
        return result

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a"""
        result = a - b
        self.history.append(('subtract', a, b, result))
        return result

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        result = a * b
        self.history.append(('multiply', a, b, result))
        return result

    def divide(self, a: float, b: float) -> float:
        """
        Divide a by b

        Args:
            a: Numerator
            b: Denominator

        Returns:
            float: Quotient of a divided by b

        Raises:
            ZeroDivisionError: If b is zero
        """
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        result = a / b
        self.history.append(('divide', a, b, result))
        return result

    def store_memory(self, value: float) -> None:
        """Store a value in calculator memory"""
        self.memory = value

    def recall_memory(self) -> float:
        """Recall the value stored in calculator memory"""
        return self.memory

    def clear_memory(self) -> None:
        """Clear calculator memory"""
        self.memory = 0.0

    def clear_history(self) -> None:
        """Clear calculation history"""
        self.history = []

    def get_history(self) -> List:
        """Get the calculation history"""
        return self.history.copy()
