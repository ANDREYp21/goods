import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
import json
import re

URL = "https://expert-autoservice.ru/get_price?p=3af702b45d2f435c864ea95a2cbeeb04&FranchiseeId=4958296"
JSON_FILE = "products.json"


def fetch_xml(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    session = requests.Session()

    retries = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=5,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    resp = session.get(
        url,
        headers=headers,
        timeout=(20, 180),  # 20s SSL, 180s чтение тела
    )

    resp.raise_for_status()

    xml_text = resp.text.lstrip("\ufeff")  # убираем BOM
    return xml_text


def clean_xml(xml_text: str) -> str:
    # заменяем "голые" амперсанды
    return re.sub(
        r'&(?!amp;|lt;|gt;|quot;|apos;)',
        '&amp;',
        xml_text
    )


def parse_xml(xml_text: str) -> list:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print("ParseError:", e)
        print("Пробуем очистить XML…")
        xml_text = clean_xml(xml_text)
        root = ET.fromstring(xml_text)

    # категории id → название
    categories = {}
    for cat in root.findall(".//category"):
        cid = cat.get("id")
        name = (cat.text or "").strip()
        if cid:
            categories[cid] = name

    products = []

    for offer in root.findall(".//offer"):
        try:
            product = {
                "id": offer.get("id") or "",
                "name": (offer.findtext("name") or "").strip(),
                "brand": (offer.findtext("vendor") or "").strip(),
                "vendorCode": (offer.findtext("vendorCode") or "").strip(),
                "category": categories.get(
                    (offer.findtext("categoryId") or "").strip(),
                    (offer.findtext("categoryId") or "").strip()
                ),
                "picture": "",
                "url": (offer.findtext("url") or "").strip(),
            }

            pictures = [
                (pic.text or "").strip()
                for pic in offer.findall("picture")
                if pic.text
            ]
            if pictures:
                product["picture"] = pictures[0]

            products.append(product)

        except Exception as e:
            print(f"Ошибка в оффере {offer.get('id')}: {e}")
            continue

    return products


def save_json(products: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"✔ Сохранено товаров: {len(products)} → {path}")


def main():
    print("⏳ Загружаем YML…")
    xml_text = fetch_xml(URL)
    print(f"✔ YML загружен ({len(xml_text) / 1024 / 1024:.2f} MB)")

    print("⏳ Парсим XML…")
    products = parse_xml(xml_text)

    print("⏳ Сохраняем JSON…")
    save_json(products, JSON_FILE)


if __name__ == "__main__":
    main()
