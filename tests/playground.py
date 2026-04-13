def calculate_discount(price: float, discount_percentage: float) -> float:
    \"\"\"
    Applies a discount to a price.
    Bug: It divides instead of subtracting the percentage!
    \"\"\"
    return price / (discount_percentage / 100)
