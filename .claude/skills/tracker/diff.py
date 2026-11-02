"""Diff двух прогонов tracker: сопоставляет товары по url и сравнивает поля.

Использование: python3 -I diff.py PREV.json CURR.json
PREV.json можно не передавать (первый запуск) — тогда все товары будут "new".

Печатает JSON-список, по одному элементу на товар из текущего прогона:
  {"url", "status": "new" | "same" | "changed",
   "prev_available", "curr_available",
   "changes": [{"field", "old", "new", "pct"}]}
pct — относительное изменение цены в %, только когда old и new — числа.
Значимость здесь не оценивается — её определяют правила из KNOWLEDGE.md.
"""
import json
import sys

FIELDS = ("regular_price", "sale_price", "has_credit")
PRICE_FIELDS = ("regular_price", "sale_price")


def load_items(path):
    with open(path, encoding="utf-8") as f:
        return {item["url"]: item for item in json.load(f)["items"]}


def is_available(item):
    return any(item.get(f) is not None for f in PRICE_FIELDS)


def pct(old, new):
    if old in (None, 0) or new is None or isinstance(old, bool):
        return None
    return round((new - old) / old * 100, 1)


def diff(prev, curr):
    result = []
    for url, cur in curr.items():
        old = prev.get(url)
        if old is None:
            result.append({"url": url, "status": "new", "prev_available": None,
                           "curr_available": is_available(cur), "changes": []})
            continue
        changes = []
        for f in FIELDS:
            if old.get(f) != cur.get(f):
                change = {"field": f, "old": old.get(f), "new": cur.get(f)}
                if f in PRICE_FIELDS:
                    change["pct"] = pct(old.get(f), cur.get(f))
                changes.append(change)
        result.append({"url": url, "status": "changed" if changes else "same",
                       "prev_available": is_available(old),
                       "curr_available": is_available(cur), "changes": changes})
    return result


if __name__ == "__main__":
    curr = load_items(sys.argv[-1])
    prev = load_items(sys.argv[1]) if len(sys.argv) == 3 else {}
    json.dump(diff(prev, curr), sys.stdout, ensure_ascii=False, indent=2)
    print()
