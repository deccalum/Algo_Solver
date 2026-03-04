import time

def log(component: str, message: str):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{component} {timestamp}] {message}")


def format_price(value: float) -> str:
    """Format price with dollar sign and thousands separator: $X XXX.XX"""
    return f"${value:,.2f}".replace(',', ' ')


def format_number(value: float) -> str:
    """Format large numbers with thousands separator: X XXX"""
    if value == int(value):
        return f"{int(value):,}".replace(',', ' ')
    return f"{value:,.2f}".replace(',', ' ')


def format_volume(value: float) -> str:
    """
    Format volume with cm³/m³ units and smart conversion.
    Uses m³ for values >= 1000000 cm³ (1 m³), otherwise cm³.
    """
    if value >= 1_000_000:
        m3_value = value / 1_000_000
        return f"{format_number(m3_value)} m³"
    return f"{format_number(value)} cm³"