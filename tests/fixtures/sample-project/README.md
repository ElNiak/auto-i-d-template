# Sample Calculator Project

A simple Python calculator library for testing RFC document generation.

## Overview

This project demonstrates a well-documented Python library that can be used
to test the RFC documentation generator. It includes:

- Public APIs with comprehensive docstrings
- Type hints for all functions
- Error handling examples
- State management (memory, history)

## Features

- Basic arithmetic operations (add, subtract, multiply, divide)
- Memory storage and recall
- Calculation history tracking
- IEEE 754 floating-point arithmetic compliance

## Usage

```python
from calculator import Calculator

calc = Calculator()
result = calc.calculate_total([1, 2, 3, 4, 5])
print(f"Total: {result}")  # Output: Total: 15.0
```

## Architecture

The Calculator class maintains internal state including:
- **memory**: Storage for a single numeric value
- **history**: List of all performed calculations

All operations are logged to history for audit purposes.

## Standards Compliance

This implementation follows:
- Python PEP 8 style guidelines
- IEEE 754 floating-point arithmetic
- Type hinting per PEP 484

## License

MIT License - Test fixture for RFC generator
