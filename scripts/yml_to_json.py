import requests
import xml.etree.ElementTree as ET
import json
import re
import time

URL = "https://expert-autoservice.ru/get_price?p=3af702b45d2f435c864ea95a2cbeeb04&FranchiseeId=4958296"
JSON_FILE = "products.json"


def fetch_xml(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    print("⏳ Начинаем загрузку YML…")

    start_time = time.time()
    chunks = []
    total = 0

    with requests.get(
        url,
        headers=headers,
        timeout=(20, 300),
        stream=True
    ) as resp:
        resp.raise_for_status()

        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue

            chunks.append(chunk)
            total += len(chunk)

            mb = total / 1024 / 1024
            elapsed = time.time() - start_time
            speed = mb / elapsed if elapsed > 0 else 0

            print(f"⬇ Загружено: {mb:.1f} MB | {speed:.2f} MB/s")

            # защита от вечного зависания
            if elapsed > 240:
                raise TimeoutError("YML грузится слишком долго (>4 минут)")

    xml_text = b"".join(chunks).decode("utf-8", errors="replace")
    print(f"✔ Загрузка завершена: {mb:.1f} MB")

    return xml_text.lstrip("\ufeff")


def clean_xml(xml_text: str) -> str:
    return re.sub(
        r'&(?!amp;|lt;|gt;|quot;|apos;)',
        '&amp;',
        xml_text
    )


def parse_xml(xml_text: str) -> list:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print("⚠ ParseError:", e)
        print("⏳ Пробуем очистить XML…")
        xml_text = clean_xml(xml_text)
        root = ET.fromstring(xml_text)

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
            print(f"⚠ Ошибка в оффере {offer.get('id')}: {e}")
            continue

    print(f"✔ Распарсено товаров: {len(products)}")
    return products


def save_json(products: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"✔ JSON сохранён → {path}")


def main():
    xml_text = fetch_xml(URL)
    products = parse_xml(xml_text)
    save_json(products, JSON_FILE)


if __name__ == "__main__":
    main()
