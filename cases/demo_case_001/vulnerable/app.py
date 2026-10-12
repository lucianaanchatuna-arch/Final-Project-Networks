def calculate(expression):
    """
    Vulnerable calculator.

    Security problem:
    This function uses eval(), which can execute arbitrary Python code.
    """
    return eval(expression)
