import re
from requests_html import HTMLSession


def find_page_count(session, url):
    r = session.get(url, verify=False)

    nav = r.html.find("nav.jet-woo-builder-shop-pagination", first=True)

    page_links = nav.find("a.page-numbers", first=False)

    max_page = 1
    for link in page_links:
        href = link.attrs.get("href", "")
        match = re.search(r"/page/(\d+)/", href)
        if match:
            page_num = int(match.group(1))
            max_page = max(max_page, page_num)

    return max_page


def get_item_details(session, url):
    r = session.get(url, verify=False)

    tr = r.html.find("tr.attribute-vaelg-pakkestoerrelse", first=True)
    if not tr:
        tr_list = r.html.find("tr.attribute-pakkestoerrelse", first=False)
        if not tr_list:
            raise ValueError("No attribute row found in the response.")
        tr = tr_list[0]  # pick the first match

    td = tr.find("td.value", first=True)
    if not td:
        raise ValueError("No value cell found in the attribute row.")

    divs = td.find("div", first=False)
    if not divs:
        raise ValueError("No divs found in the value cell.")

    last_text = divs[-1].text.strip()

    match = re.match(
        r"^([\d.,]+\s*(?:gram|kg|g))\s*=\s*([\d.,-]+)",
        last_text,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError("No match found for weight and price in the last option.")

    weight_str = match.group(1).strip().lower()
    weight_str_cleaned = weight_str.replace(".", "").replace(",", ".")
    weight_val = float(re.sub(r"[^\d.]", "", weight_str_cleaned))

    if "kg" in weight_str:
        pass  # already in kg
    elif "g" in weight_str:
        if weight_val <= 50:
            pass  # treat as kg
        else:
            weight_val = weight_val / 1000  # real grams, convert to kg
    else:
        raise ValueError("could not determine weight")

    price_str = match.group(2).strip()
    price_val = int(re.sub(r"[^\d]", "", price_str))

    return {
        "weight": weight_val,
        "price": price_val,
    }


def main():
    URL = "https://www.kodbilen.dk/varer/carnivore/"
    URL = "https://www.kodbilen.dk/varer/dagstilbud/"
    URL = "https://www.kodbilen.dk/varer/kalv-og-koedkvaeg/"

    session = HTMLSession()

    item_links = []
    page_count = find_page_count(session, URL)
    for page in range(1, page_count + 1):
        r = session.get(
            f"{URL}/page/{page}/",
            verify=False,
        )

        buttons = r.html.find(
            "a.jet-button__instance.jet-button__instance--icon-left.hover-effect-0"
        )
        item_links = item_links + [href.attrs.get("href") for href in buttons]

    results = []
    failures = []
    for item_link in item_links:
        try:
            item = get_item_details(session, item_link)
            results.append(
                {
                    "link": item_link,
                    "weight": item["weight"],
                    "price": item["price"],
                    "price_per_kg": item["price"] / item["weight"],
                }
            )
        except ValueError:
            failures.append(item_link)

    for item in failures:
        print(f"Failed to parse item: {item}")

    top5 = sorted(results, key=lambda x: x["price_per_kg"])[:5]
    for i, item in enumerate(top5, 1):
        print(f"{i}. {item['link']}")
        print(f"   Weight: {item['weight']} kg")
        print(f"   Price: {item['price']} DKK")
        print(f"   Price per kg: {item['price_per_kg']:.2f} DKK/kg")


def test(url):
    session = HTMLSession()
    res = get_item_details(session, url)
    print(
        {
            "url": url,
            "weight": res["weight"],
            "price": res["price"],
            "price_per_kg": res["price"] / res["weight"],
        }
    )


if __name__ == "__main__":
    # test("https://www.kodbilen.dk/vare/oekologisk-hakket-oksekoed-20-25-frost/")
    main()
