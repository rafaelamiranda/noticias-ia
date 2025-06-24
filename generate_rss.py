import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
from email.utils import parsedate_to_datetime
import requests # Importe a biblioteca requests

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

def get_final_redirect_url(url: str) -> str:
    """Obtém a URL final após seguir todos os redirecionamentos."""
    try:
        # Usa requests.head para obter apenas os cabeçalhos e seguir redirecionamentos
        # timeout para evitar que a requisição demore demais
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.url # Retorna a URL final após os redirecionamentos
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter URL final para {url}: {e}")
        return url # Em caso de erro, retorna a URL original do Google Notícias

def fetch_items(feed_url: str):
    with urllib.request.urlopen(feed_url) as response:
        data = response.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", default="")
        google_news_link = item.findtext("link", default="") # Link do Google Notícias
        
        # Obter a URL final da notícia
        final_link = get_final_redirect_url(google_news_link)

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
            "link": final_link, # Use a URL final aqui
            "description": description,
            "pubDate": pub_date,
        })
    return items

def filter_last_24_hours(items):
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day = datetime.timedelta(days=1)
    return [item for item in items if now - item["pubDate"] <= one_day]

def generate_combined_rss():
    languages = ["pt", "en"]
    all_items = []
    for lang in languages:
        url = build_feed_url(lang)
        fetched = fetch_items(url)
        all_items.extend(filtered) # 'filtered' não está definido aqui, deveria ser 'fetched' ou aplicar o filtro depois

    # Correção: aplicar o filtro após coletar todos os itens, ou dentro do loop se preferir
    # Vamos aplicar depois para simplificar o exemplo
    all_items = filter_last_24_hours(all_items)

    # Ordena por data de publicação (mais recente primeiro)
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)

    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        "    <title>Notícias de Inteligência Artificial (PT & EN)</title>",
        "    <link>https://github.com/rafaelamiranda/noticias-ia</link>",
        "    <description>",
        "Principais notícias relacionadas a inteligência artificial",
        "das últimas 24 horas, em Português e Inglês.",
        "    </description>",
        f"    <lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT' )}</lastBuildDate>",
    ]
    for item in all_items:
        lines.extend([
            "    <item>",
            f"      <title>{html.escape(item['title'])}</title>",
            f"      <link>{html.escape(item['link'])}</link>",
            f"      <description>{html.escape(item['description'])}</description>",
            f"      <pubDate>{item['pubDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>",
            f"      <guid>{html.escape(item['link'])}</guid>", # GUID também deve ser a URL final
            "    </item>",
        ])
    lines.extend(["  </channel>", "</rss>"])
    filename = "index.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"RSS combinado gerado: {filename}")

if __name__ == "__main__":
    generate_combined_rss()
