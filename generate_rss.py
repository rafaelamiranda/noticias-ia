import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
from email.utils import parsedate_to_datetime

FEED_URL = (
    "https://news.google.com/rss/search?q=intelig%C3%AAncia+artificial&hl=pt-BR&gl=BR&ceid=BR:pt-419"
)

MAX_DESCRIPTION = 90


def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()


def _short(text: str, max_len: int = MAX_DESCRIPTION) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def fetch_items():
    with urllib.request.urlopen(FEED_URL) as response:
        data = response.read()

    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        desc_raw = item.findtext("description", default="")
        description = _short(_clean_html(desc_raw))
        pub_date_str = item.findtext("pubDate")
        try:
            pub_date = parsedate_to_datetime(pub_date_str).astimezone(
                datetime.timezone.utc
            )
        except Exception:
            pub_date = datetime.datetime.now(datetime.timezone.utc)
        items.append({
            "title": title,
            "link": link,
            "description": description,
            "pubDate": pub_date,
        })
    return items


def filter_last_24_hours(items):
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day = datetime.timedelta(days=1)
    return [item for item in items if now - item["pubDate"] <= one_day]


def generate_rss():
    all_items = fetch_items()
    news_items = filter_last_24_hours(all_items)
    now = datetime.datetime.now(datetime.timezone.utc)

    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        "    <title>Notícias de Inteligência Artificial</title>",
        "    <link>https://github.com/rafaelamiranda/noticias-ia</link>",
        "    <description>Principais notícias relacionadas a inteligência artificial das últimas 24 horas.</description>",
        f"    <lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>",
    ]

    for item in news_items:
        lines.extend(
            [
                "    <item>",
                f"      <title>{html.escape(item['title'])}</title>",
                f"      <link>{html.escape(item['link'])}</link>",
                f"      <description>{html.escape(item['description'])}</description>",
                f"      <pubDate>{item['pubDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>",
                f"      <guid>{html.escape(item['link'])}</guid>",
                "    </item>",
            ]
        )

    lines.extend(["  </channel>", "</rss>"])

    with open("index.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    generate_rss()
