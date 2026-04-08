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


def sanitize_item_id(raw_id):
    """Heureka ITEM_ID: jen čísla, písmena bez diakritiky, podtržítka, pomlčky."""
    clean = raw_id.replace("/", "-")
    clean = re.sub(r"[^a-zA-Z0-9_-]", "", clean)
    return clean


def get_delivery_date(availability):
    if availability == "in_stock":
        return "0"
    if availability == "preorder":
        return "14"
    return "7"


def strip_price(price_text):
    """Odstraní měnu a vrátí jen číslo."""
    return re.sub(r"[^\d.,]", "", price_text).strip()


def map_heureka_category(product_type):
    """Mapuj GMC product_type na Heureka kategorie."""
    pt = (product_type or "").strip().lower()
    if "interiér" in pt or "interier" in pt:
        return "Dům a zahrada | Krby a kamna | Koše na dřevo a krbové příslušenství"
    elif "bar" in pt:
        return "Dům a zahrada | Zahradní nábytek a doplňky | Zahradní bary"
    else:
        return "Dům a zahrada | Krby a kamna | Koše na dřevo a krbové příslušenství"


def parse_params(item):
    """Extrahuje PARAM z g:product_detail."""
    params = []
    for detail in item.findall(".//g:product_detail", NS):
        attr_name = detail.findtext("g:attribute_name", "", NS).strip()
        attr_value = detail.findtext("g:attribute_value", "", NS).strip()
        if not attr_name or not attr_value:
            continue
        if attr_name == "Značka":
            continue
        name = attr_name.lstrip("> ").strip()
        params.append((name, attr_value))
    return params


def build_description(title, custom_label, params):
    """Sestav delší popis min 50 znaků pro Heureka."""
    parts = [title]
    if custom_label:
        parts.append(custom_label)
    param_strs = [f"{n}: {v}" for n, v in params]
    if param_strs:
        parts.append(". ".join(param_strs))
    parts.append(
        "Modulární ocelový dřevník z práškově lakované oceli. "
        "Snadná montáž bez sváření. Česká výroba, skladem."
    )
    return " | ".join(parts)


def get_text(item, tag):
    el = item.find(f"g:{tag}", NS)
    return el.text.strip() if el is not None and el.text else ""


# --- Main ---
print("Stahuji GMC feed...")
resp = requests.get(GMC_URL)
resp.raise_for_status()
root = ET.fromstring(resp.content)
items = root.findall(".//item")
print(f"Nalezeno {len(items)} produktů")

lines = ['<?xml version="1.0" encoding="utf-8"?>', "<SHOP>"]

for item in items:
    raw_id = get_text(item, "id")
    title = get_text(item, "title")
    if not raw_id or not title:
        continue

    clean_id = sanitize_item_id(raw_id)
    url = get_text(item, "link")
    img = get_text(item, "image_link")
    price_raw = get_text(item, "price")
    price = strip_price(price_raw) if price_raw else ""
    availability = get_text(item, "availability")
    delivery = get_delivery_date(availability)
    brand = get_text(item, "brand")
    product_type = get_text(item, "product_type")
    custom_label = get_text(item, "custom_label_0")

    heureka_cat = map_heureka_category(product_type)
    params = parse_params(item)
    description = build_description(title, custom_label, params)

    product_text = f"{title} — {custom_label}" if custom_label else title

    lines.append("  <SHOPITEM>")
    lines.append(f"    <ITEM_ID>{clean_id}</ITEM_ID>")
    lines.append(f"    <PRODUCTNAME>{cdata(title)}</PRODUCTNAME>")
    lines.append(f"    <PRODUCT>{cdata(product_text)}</PRODUCT>")
    lines.append(f"    <DESCRIPTION>{cdata(description)}</DESCRIPTION>")
    lines.append(f"    <URL>{cdata(url)}</URL>")
    if img:
        lines.append(f"    <IMGURL>{cdata(img)}</IMGURL>")
    lines.append(f"    <PRICE_VAT>{price}</PRICE_VAT>")
    lines.append(f"    <VAT>21</VAT>")
    lines.append(f"    <CATEGORYTEXT>{cdata(heureka_cat)}</CATEGORYTEXT>")
    if brand:
        lines.append(f"    <MANUFACTURER>{cdata(brand)}</MANUFACTURER>")
    lines.append(f"    <DELIVERY_DATE>{delivery}</DELIVERY_DATE>")
    for pname, pval in params:
        lines.append("    <PARAM>")
        lines.append(f"      <PARAM_NAME>{cdata(pname)}</PARAM_NAME>")
        lines.append(f"      <VAL>{cdata(pval)}</VAL>")
        lines.append("    </PARAM>")
    lines.append("  </SHOPITEM>")

lines.append("</SHOP>")

xml_output = "\n".join(lines) + "\n"
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(xml_output)
print(f"Hotovo — {len(items)} produktů → {OUTPUT}")
