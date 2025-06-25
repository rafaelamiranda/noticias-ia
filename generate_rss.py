import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import time


def _clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()


def _fetch_full_article(url: str) -> str:
    """Busca o conteúdo completo do artigo a partir da URL."""
    try:
        # Adiciona timeout e user-agent para evitar bloqueios
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
        
        # Extrai o conteúdo principal usando heurísticas simples
        # Remove scripts, styles e outros elementos desnecessários
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<nav[^>]*>.*?</nav>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<header[^>]*>.*?</header>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<footer[^>]*>.*?</footer>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Busca por tags comuns de conteúdo de artigo
        article_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
            r'<main[^>]*>(.*?)</main>',
        ]
        
        content = ""
        for pattern in article_patterns:
            match = re.search(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1)
                break
        
        # Se não encontrou nenhum padrão específico, pega o body
        if not content:
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, flags=re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1)
        
        # Limpa o HTML e retorna apenas o texto
        clean_content = _clean_html(content)
        
        # Limita o tamanho para evitar RSS muito grande (máximo 2000 caracteres)
        if len(clean_content) > 2000:
            clean_content = clean_content[:1997] + "..."
            
        return clean_content if clean_content else "Conteúdo não disponível"
        
    except Exception as e:
        print(f"Erro ao buscar artigo {url}: {e}")
        return "Conteúdo não disponível"





def _escape_xml(text: str) -> str:
    """Escapa caracteres especiais para XML, incluindo & em URLs."""
    if not text:
        return ""
    # Usar html.escape com quote=True para escapar aspas também
    return html.escape(text, quote=True)


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
        
        # Busca o conteúdo completo do artigo
        print(f"Buscando conteúdo de: {title[:50]}...")
        full_content = _fetch_full_article(link)
        
        # Se não conseguiu buscar o conteúdo completo, usa a descrição original
        description = full_content if full_content != "Conteúdo não disponível" else _clean_html(desc_raw)
        
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
        
        # Adiciona uma pequena pausa para não sobrecarregar os servidores
        time.sleep(0.5)
        
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
        filtered = filter_last_24_hours(fetched)
        all_items.extend(filtered)

    # Ordena por data de publicação (mais recente primeiro)
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)

    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        "    <title>Notícias de Inteligência Artificial (PT &amp; EN)</title>",
        "    <link>https://github.com/rafaelamiranda/noticias-ia</link>",
        "    <description>",
        "Principais notícias relacionadas a inteligência artificial",
        "das últimas 24 horas, em Português e Inglês.",
        "    </description>",
        f"    <lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>",
    ]
    for item in all_items:
        lines.extend([
            "    <item>",
            f"      <title>{_escape_xml(item['title'])}</title>",
            f"      <link>{_escape_xml(item['link'])}</link>",
            f"      <description>{_escape_xml(item['description'])}</description>",
            f"      <pubDate>{item['pubDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>",
            f"      <guid>{_escape_xml(item['link'])}</guid>",
            "    </item>",
        ])
    lines.extend(["  </channel>", "</rss>"])
    filename = "index.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"RSS combinado gerado: {filename}")


if __name__ == "__main__":
    generate_combined_rss()