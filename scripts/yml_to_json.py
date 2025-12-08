import requests
import xml.etree.ElementTree as ET
import json
import re

URL = "https://expert-autoservice.ru/get_price?p=3af702b45d2f435c864ea95a2cbeeb04&FranchiseeId=4958296"
JSON_FILE = "products.json"

def fetch_xml(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    xml_text = resp.text.lstrip("\ufeff")  # убираем BOM если есть
    return xml_text

def clean_xml(xml_text: str) -> str:
    # заменяем голые амперсанды на &amp;
    xml_text = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', xml_text)
    return xml_text

def parse_xml(xml_text: str) -> list:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print("ParseError:", e)
        print("Попробуем очистить XML…")
        xml_text = clean_xml(xml_text)
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
        try:
            oid = offer.get("id") or ""
            name = (offer.findtext("name") or "").strip()
            vendor = (offer.findtext("vendor") or "").strip()
            vendor_code = (offer.findtext("vendorCode") or "").strip()   # ← артикул
            category_id = (offer.findtext("categoryId") or "").strip()
            category_name = categories.get(category_id, category_id)

            pictures = [(pic.text or "").strip() for pic in offer.findall("picture") if pic.text]
            picture = pictures[0] if pictures else ""

            url = (offer.findtext("url") or "").strip()
            price = (offer.findtext("price") or "").strip()
            currency = (offer.findtext("currencyId") or "").strip()

            product = {
    "id": oid,
    "name": name,
    "brand": vendor,
    "vendorCode": vendor_code,
    "category": category_name,
    "picture": picture,
    "url": url
}
            products.append(product)
        except Exception as e:
            print(f"Ошибка в оффере {offer.get('id')}: {e}")
            continue  # пропускаем битый оффер

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
