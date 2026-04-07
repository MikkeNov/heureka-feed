#!/usr/bin/env python3
"""Stáhne GMC feed a převede ho na Heureka XML formát."""

import re
import requests
import xml.etree.ElementTree as ET

GMC_URL = (
    "https://www.drevnikovesteny.cz/gmc.xml"
    "?feed_id=3&access_token=075ef03b41ee435186c08660967d1d2e"
)
OUTPUT = "docs/heureka_feed.xml"

NS = {"g": "http://base.google.com/ns/1.0"}


def cdata(text):
    """Vrátí text obalený v CDATA."""
    return f"<![CDATA[{text}]]>"


def get_delivery_date(availability):
    if availability == "in_stock":
        return "0"
    if availability == "preorder":
        return "14"
    return "7"


def strip_price(price_text):
    """Odstraní měnu a vrátí jen číslo."""
    return re.sub(r"[^\d.,]", "", price_text).strip()


def convert_category(product_type):
    """Převede GMC kategorii na Heureka formát s prefixem."""
    if not product_type:
        return ""
    # Nahraď " > " za " | "
    converted = product_type.replace(" > ", " | ")
    return f"Dům a zahrada | Zahradní nábytek a doplňky | {converted}"


def parse_params(item):
    """Extrahuje PARAM z g:product_detail."""
    params = []
    for detail in item.findall(".//g:product_detail", NS):
        attr_name = detail.findtext("g:attribute_name", "", NS).strip()
        attr_value = detail.findtext("g:attribute_value", "", NS).strip()
        if not attr_name or not attr_value:
            continue
        # Přeskoč atribut "Značka"
        if attr_name == "Značka":
            continue
        # Ořež "> " z názvu atributu
        if attr_name.startswith("> "):
            attr_name = attr_name[2:]
        params.append((attr_name, attr_value))
    return params


def build_shopitem_xml(item):
    """Sestaví XML řetězec pro jeden SHOPITEM."""
    item_id = item.findtext("g:id", "", NS).strip()
    title = item.findtext("g:title", "", NS).strip()
    custom_label_0 = item.findtext("g:custom_label_0", "", NS).strip()
    link = item.findtext("g:link", "", NS).strip()
    image_link = item.findtext("g:image_link", "", NS).strip()
    price = item.findtext("g:price", "", NS).strip()
    product_type = item.findtext("g:product_type", "", NS).strip()
    brand = item.findtext("g:brand", "", NS).strip()
    availability = item.findtext("g:availability", "", NS).strip()

    # Složený popis = title + custom_label_0
    product_desc = f"{title} {custom_label_0}".strip() if custom_label_0 else title

    lines = []
    lines.append("    <SHOPITEM>")
    lines.append(f"      <ITEM_ID>{item_id}</ITEM_ID>")
    lines.append(f"      <PRODUCTNAME>{cdata(title)}</PRODUCTNAME>")
    lines.append(f"      <PRODUCT>{cdata(product_desc)}</PRODUCT>")
    lines.append(f"      <DESCRIPTION>{cdata(custom_label_0)}</DESCRIPTION>")
    lines.append(f"      <URL>{cdata(link)}</URL>")
    lines.append(f"      <IMGURL>{cdata(image_link)}</IMGURL>")
    lines.append(f"      <PRICE_VAT>{strip_price(price)}</PRICE_VAT>")
    lines.append("      <VAT>21</VAT>")

    if product_type:
        cat = convert_category(product_type)
        lines.append(f"      <CATEGORYTEXT>{cdata(cat)}</CATEGORYTEXT>")

    if brand:
        lines.append(f"      <MANUFACTURER>{cdata(brand)}</MANUFACTURER>")

    delivery = get_delivery_date(availability)
    lines.append(f"      <DELIVERY_DATE>{delivery}</DELIVERY_DATE>")

    for name, value in parse_params(item):
        lines.append("      <PARAM>")
        lines.append(f"        <PARAM_NAME>{cdata(name)}</PARAM_NAME>")
        lines.append(f"        <VAL>{cdata(value)}</VAL>")
        lines.append("      </PARAM>")

    lines.append("    </SHOPITEM>")
    return "\n".join(lines)


def main():
    print("Stahuji GMC feed...")
    resp = requests.get(GMC_URL, timeout=60)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = root.findall(".//item")
    print(f"Nalezeno {len(items)} produktů.")

    shop_items = []
    for item in items:
        shop_items.append(build_shopitem_xml(item))

    xml_output = '<?xml version="1.0" encoding="utf-8"?>\n<SHOP>\n'
    xml_output += "\n".join(shop_items)
    xml_output += "\n</SHOP>\n"

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(xml_output)

    print(f"Feed uložen do {OUTPUT} ({len(items)} položek).")


if __name__ == "__main__":
    main()
