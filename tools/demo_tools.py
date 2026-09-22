"""PLACEHOLDER tools. The SDK infers schemas from these types and docstrings."""

import json
import math
import sqlite3
from typing import Literal

from agents import RunContextWrapper, function_tool
from agents.exceptions import ModelBehaviorError

import db


def tool_error(context: RunContextWrapper, error: Exception) -> str:
    """Give the model and UI a safe failure result, without raw exception text."""
    if isinstance(error, sqlite3.Error):
        message = "Database operation failed. Check app.db permissions and file locks."
    elif isinstance(error, (ValueError, ModelBehaviorError)):
        message = "Invalid arguments. Check the tool's required fields and allowed values."
    else:
        message = "Tool failed unexpectedly. Check its implementation before retrying."
    return json.dumps({"ok": False, "error": message, "error_type": type(error).__name__})


@function_tool(failure_error_function=tool_error)
def list_demo_items() -> dict:
    """Read all placeholder items, including their IDs, names, and numeric values."""
    return {"ok": True, "items": db.list_demo_items()}


@function_tool(failure_error_function=tool_error)
def save_note(text: str) -> dict:
    """Save a local demonstration note and return its ID.

    Args:
        text: Nonblank note, at most 2000 characters after trimming whitespace.
    """
    return {"ok": True, "note_id": db.save_note(text)}


@function_tool(failure_error_function=tool_error)
def calculate(operation: Literal["add", "subtract", "multiply", "divide"],
              a: float, b: float) -> dict:
    """Calculate a deterministic arithmetic result using two finite numbers.

    Args:
        operation: Arithmetic operation to perform on a and b, in that order.
        a: First finite number.
        b: Second finite number; must be nonzero for division.
    """
    if not math.isfinite(a) or not math.isfinite(b):
        return {"ok": False, "error": "Both numbers must be finite."}
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"ok": False, "error": "Cannot divide by zero."}
        result = a / b
    else:
        return {"ok": False, "error": "Unsupported arithmetic operation."}
    if not math.isfinite(result):
        return {"ok": False, "error": "Result is too large for a finite number."}
    return {"ok": True, "result": result}
