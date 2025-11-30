import requests
import xml.etree.ElementTree as ET
import json

URL = "https://expert-autoservice.ru/get_price?p=4c1d94f02eb649b4810b60ef85132f4c&FranchiseeId=4958296"
JSON_FILE = "products.json"

def yml_to_json(url, json_file):
    xml_data = requests.get(url).text
    root = ET.fromstring(xml_data)

    categories = {c.get("id"): c.text.strip() for c in root.findall(".//category") if c.text}

    products = []
    for offer in root.findall(".//offer"):
        products.append({
            "id": offer.get("id"),
            "name": offer.findtext("name", "").strip(),
            "brand": offer.findtext("vendor", "").strip(),
            "category": categories.get(offer.findtext("categoryId", ""), ""),
            "picture": offer.findtext("picture", "").strip(),
            "url": offer.findtext("url", "").strip(),
            "price": offer.findtext("price", "").strip(),
            "currency": offer.findtext("currencyId", "").strip()
        })

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    yml_to_json(URL, JSON_FILE)
