import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
import argparse
from email.utils import parsedate_to_datetime

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

def build_feed_url(lang: str) -> str:
    """Retorna a URL do RSS com base no idioma."""
    if lang == "en":
        query = "artificial+intelligence"
        hl = "en-US"
        gl = "US"
        ceid = "US:en"
    else:
        query = "intelig%C3%AAncia+artificial"
        hl = "pt-BR"
        gl = "BR"
        ceid = "BR:pt-419"
    return (
        f"https://news.google.com/rss/search?"
        f"q={query}&hl={hl}&gl={gl}&ceid={ceid}"
    )

def fetch_items(feed_url: str):
    with urllib.request.urlopen(feed_url) as response:
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

def generate_rss(lang: str):
    feed_url = build_feed_url(lang)
    all_items = fetch_items(feed_url)
    news_items = filter_last_24_hours(all_items)
    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        f"    <title>Notícias de Inteligência Artificial ({lang})</title>",
        "    <link>https://github.com/rafaelamiranda/noticias-ia</link>",
        "    <description>"
        "Principais notícias relacionadas a inteligência artificial"
        f" das últimas 24 horas ({lang})."
        "</description>",
        f"    <lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>",
    ]
    for item in news_items:
        lines.extend([
            "    <item>",
            f"      <title>{html.escape(item['title'])}</title>",
            f"      <link>{html.escape(item['link'])}</link>",
            f"      <description>{html.escape(item['description'])}</description>",
            f"      <pubDate>{item['pubDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>",
            f"      <guid>{html.escape(item['link'])}</guid>",
            "    </item>",
        ])
    lines.extend(["  </channel>", "</rss>"])
    filename = f"index_{lang}.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"RSS gerado: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gera RSS de notícias de IA (PT ou EN)."
    )
    parser.add_argument(
        "--lang",
        choices=["pt", "en"],
        default="pt",
        help="Idioma da busca: 'pt' para português ou 'en' para inglês."
    )
    args = parser.parse_args()
    generate_rss(args.lang)
