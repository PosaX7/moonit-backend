# backend/Moonit_backend/utils/formatters.py
def format_montant(value: float | int) -> str:
    """Renvoie le nombre avec séparateur de milliers, ex: 2000 -> '2 000'"""
    if value is None:
        return "0"
    return f"{int(value):,}".replace(",", " ")
