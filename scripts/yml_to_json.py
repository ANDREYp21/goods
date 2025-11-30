import requests
import xml.etree.ElementTree as ET
import json

URL = "https://expert-autoservice.ru/get_price?p=3af702b45d2f435c864ea95a2cbeeb04&FranchiseeId=4958296"
JSON_FILE = "products.json"

def fetch_xml(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    xml_text = resp.text.lstrip("\ufeff")  # убираем BOM если есть
    return xml_text

def parse_xml(xml_text: str) -> list:
    root = ET.fromstring(xml_text)

    # словарь категорий id → название
    categories = {}
    for cat in root.findall(".//category"):
        cid = cat.get("id")
        name = (cat.text or "").strip()
        if cid:
            categories[cid] = name

    products = []
    for offer in root.findall(".//offer"):
        oid = offer.get("id") or ""
        name = (offer.findtext("name") or "").strip()
        vendor = (offer.findtext("vendor") or "").strip()
        category_id = (offer.findtext("categoryId") or "").strip()
        category_name = categories.get(category_id, category_id)

        # несколько картинок
        pictures = [ (pic.text or "").strip() for pic in offer.findall("picture") if pic.text ]
        picture = pictures[0] if pictures else ""

        url = (offer.findtext("url") or "").strip()
        price = (offer.findtext("price") or "").strip()
        currency = (offer.findtext("currencyId") or "").strip()

        product = {
            "id": oid,
            "name": name,
            "brand": vendor,
            "category": category_name,
            "picture": picture,
            "url": url,
            "price": price,
            "currency": currency
        }
        products.append(product)

    return products

def save_json(products: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"Сохранено товаров: {len(products)} → {path}")

def main():
    xml_text = fetch_xml(URL)
    products = parse_xml(xml_text)
    save_json(products, JSON_FILE)

if __name__ == "__main__":
    main()
