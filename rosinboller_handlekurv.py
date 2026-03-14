#!/usr/bin/env python3
"""
Automatisk handlekurv for Verdens beste rosinboller - Trines Matblogg
Oppskrift: https://trinesmatblogg.no/recipe/rosinboller/

Søker opp ingredienser på Oda, velger billigste alternativ per kg/liter,
legger alt i handlekurven og viser oppsummering med total estimert pris.

Forutsetning: Logg inn på Oda først:
  npx github:gbbirkisson/mcp-oda auth login --user din@epost.no --pass dittpassord
"""

import subprocess
import json
import sys
from typing import Optional

RECIPE_URL = "https://trinesmatblogg.no/recipe/rosinboller/"

# Ingredienser fra Trines Matblogg - Verdens beste rosinboller (ca. 20 boller)
# Kilde: https://trinesmatblogg.no/recipe/rosinboller/
INGREDIENTS = [
    {
        "search_query": "hvetemel",
        "display": "900 g hvetemel",
    },
    {
        "search_query": "helmelk",
        "display": "5 dl melk",
    },
    {
        "search_query": "fersk gjær",
        "display": "50 g fersk gjær",
    },
    {
        "search_query": "sukker",
        "display": "125 g sukker",
    },
    {
        "search_query": "malt kardemomme",
        "display": "2 ts malt kardemomme",
    },
    {
        "search_query": "smør meierismør",
        "display": "150 g smør",
    },
    {
        "search_query": "egg",
        "display": "2 egg (1 i deig + 1 til pensling)",
    },
    {
        "search_query": "rosiner",
        "display": "200 g rosiner",
    },
]

MCP_ODA_CMD = ["npx", "--yes", "github:gbbirkisson/mcp-oda"]


def run_mcp_oda(args: list[str], capture_json: bool = True) -> Optional[dict | list]:
    """Kjør mcp-oda CLI og returner output."""
    cmd = MCP_ODA_CMD + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Tidsavbrudd ved kontakt med Oda")

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Ukjent feil fra mcp-oda")

    if not capture_json or not result.stdout.strip():
        return None

    return json.loads(result.stdout)


def search_products(query: str) -> list[dict]:
    """Søk etter produkter på Oda. Returnerer liste med produkter."""
    data = run_mcp_oda(["product", "search", query])
    if isinstance(data, dict):
        return data.get("items", [])
    if isinstance(data, list):
        return data
    return []


def get_unit_price(product: dict) -> Optional[float]:
    """Hent pris per kg/liter for sammenligning."""
    return product.get("relative_price")


def find_cheapest(products: list[dict]) -> Optional[dict]:
    """Finn billigste produkt basert på pris per kg/liter.
    Faller tilbake på absolutt pris hvis enhetspris mangler."""
    if not products:
        return None

    # Foretrekk produkter med enhetspris for rettferdig sammenligning
    with_unit_price = [p for p in products if get_unit_price(p) is not None]
    candidates = with_unit_price if with_unit_price else products

    return min(
        candidates,
        key=lambda p: get_unit_price(p) if get_unit_price(p) is not None else p.get("price", float("inf")),
    )


def add_to_cart(product_id: int | str) -> bool:
    """Legg produkt i handlekurv på Oda."""
    try:
        run_mcp_oda(["product", "add", str(product_id)], capture_json=False)
        return True
    except RuntimeError as e:
        print(f"     ⚠ Klarte ikke legge i kurv: {e}")
        return False


def format_price(price: Optional[float]) -> str:
    if price is None:
        return "ukjent"
    return f"kr {price:.2f}"


def print_separator(char: str = "─", width: int = 72) -> None:
    print(char * width)


def main() -> None:
    print()
    print_separator("═")
    print("  HANDLEKURV: Verdens beste rosinboller")
    print(f"  Oppskrift: {RECIPE_URL}")
    print_separator("═")
    print()

    cart_items = []

    for ingredient in INGREDIENTS:
        query = ingredient["search_query"]
        display = ingredient["display"]

        print(f"Søker: {display}  →  query: \"{query}\"")

        try:
            products = search_products(query)
        except Exception as exc:
            print(f"  ✗ Søkefeil: {exc}")
            cart_items.append(
                {"ingredient": display, "product": "—", "price": None, "unit_price": None, "added": False}
            )
            continue

        if not products:
            print(f"  ✗ Ingen treff – prøv manuelt på oda.com")
            cart_items.append(
                {"ingredient": display, "product": "—", "price": None, "unit_price": None, "added": False}
            )
            continue

        cheapest = find_cheapest(products)
        product_name = cheapest.get("name", "Ukjent")
        product_id = cheapest.get("id")
        price = cheapest.get("price")
        unit_price = get_unit_price(cheapest)
        unit = cheapest.get("relative_price_unit", "")

        unit_str = f"  ({format_price(unit_price)}{unit})" if unit_price else ""
        print(f"  ✓ Valgt:  {product_name}")
        print(f"     Pris:  {format_price(price)}{unit_str}")

        added = add_to_cart(product_id) if product_id is not None else False

        cart_items.append(
            {
                "ingredient": display,
                "product": product_name,
                "price": price,
                "unit_price": unit_price,
                "added": added,
            }
        )
        print()

    # ── Oppsummering ──────────────────────────────────────────────────────────
    print()
    print_separator("═")
    print("  OPPSUMMERING")
    print_separator("═")

    col_ingr = 30
    col_prod = 28
    col_price = 10

    header = f"  {'Ingrediens':<{col_ingr}}  {'Produkt':<{col_prod}}  {'Pris':>{col_price}}"
    print(header)
    print_separator()

    total = 0.0
    added_count = 0

    for item in cart_items:
        status = "✓" if item["added"] else "✗"
        ingr = item["ingredient"][:col_ingr]
        prod = item["product"][:col_prod]
        price_str = format_price(item["price"])
        print(f"  {status} {ingr:<{col_ingr}}  {prod:<{col_prod}}  {price_str:>{col_price}}")
        if item["price"] is not None:
            total += item["price"]
        if item["added"]:
            added_count += 1

    print_separator()
    print(f"  {'TOTAL ESTIMERT PRIS':<{col_ingr + col_prod + 4}}  {format_price(total):>{col_price}}")
    print()
    print(f"  {added_count}/{len(INGREDIENTS)} ingredienser lagt i handlekurven")
    if added_count < len(INGREDIENTS):
        missing = [i["ingredient"] for i in cart_items if not i["added"]]
        print("  Mangler (legg til manuelt):")
        for m in missing:
            print(f"    • {m}")
    print()
    print("  Fullfør bestillingen på:  https://oda.com/no/cart/")
    print_separator("═")
    print()


if __name__ == "__main__":
    main()
