import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
from email.utils import parsedate_to_datetime
import urllib.parse
import base64

MAX_DESCRIPTION = 90


def _clean_html(text: str ) -> str:
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
    """
    Tenta obter a URL final de uma notícia do Google Notícias.
    Primeiro tenta decodificar a string CBMi.
    Se falhar, tenta analisar a tag canonical ou redirecionamentos JavaScript.
    """
    # Tenta decodificar a URL do Google Notícias (formato CBMi)
    if "news.google.com/rss/articles/CBM" in url:
        try:
            # Extrai a parte codificada em base64.
            # O padrão CBMi pode vir seguido de um '?' ou ser o final da string.
            # Também considera o formato /articles/CBM<encoded_string>
            match = re.search(r'CBM(.*?)(?:\?|$)|\/articles\/(.*?)(?:\?|$)', url)
            if match:
                # Prioriza o grupo 1 (CBM<encoded_string>?) se existir, senão o grupo 2 (/articles/<encoded_string>?)
                encoded_part = match.group(1) if match.group(1) else match.group(2)
                
                # Adiciona padding se necessário para base64 URL-safe
                missing_padding = len(encoded_part) % 4
                if missing_padding != 0:
                    encoded_part += '=' * (4 - missing_padding)
                
                decoded_bytes = base64.urlsafe_b64decode(encoded_part)
                decoded_string = decoded_bytes.decode('utf-8', errors='ignore')
                
                # Procura pela primeira URL http(s ):// na string decodificada
                # A URL real geralmente é a primeira que aparece.
                url_match = re.search(r'https?://[^\s"\']+', decoded_string )
                if url_match:
                    print(f"URL decodificada de CBMi: {url_match.group(0)}")
                    return url_match.group(0)
                else:
                    print(f"Nenhuma URL encontrada na string decodificada: {decoded_string}")

        except Exception as e:
            print(f"Erro ao decodificar CBMi URL {url}: {e}")

    # Se a decodificação CBMi falhou ou não se aplica, tenta resolver usando urllib
    try:
        with urllib.request.urlopen(url) as resp:
            final_url = resp.geturl()
            html_content = resp.read().decode("utf-8", errors="ignore")

        if "news.google.com" not in final_url:
            print(f"Redirecionamento HTTP direto para: {final_url}")
            return final_url

        # Procura tag canonical
        match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html_content, re.IGNORECASE)
        if match:
            print(f"URL canonical encontrada: {match.group(1)}")
            return match.group(1)

        # Procura window.location.href
        match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)', html_content)
        if match:
            print(f"Redirecionamento JS encontrado: {match.group(1)}")
            return match.group(1)

        # Se nada for encontrado, usa a própria URL final
        print(f"Não foi possível determinar URL final para {url}. Retornando a URL original do Google Notícias.")
        return final_url

    except Exception as e:
        print(f"Erro ao obter ou analisar URL final para {url}: {e}")
        return url


# ... (o restante do seu script generate_rss.py permanece o mesmo) ...

def fetch_items(feed_url: str):
    with urllib.request.urlopen(feed_url) as response:
        data = response.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title", default="")
        google_news_link = item.findtext("link", default="") # Link do Google Notícias
        
        print(f"URL do Google Notícias (original): {google_news_link}")
        
        # Obter a URL final da notícia
        final_link = get_final_redirect_url(google_news_link)
        
        print(f"URL final obtida: {final_link}")

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
        fetched_items = fetch_items(url)
        all_items.extend(fetched_items)

    # Aplica o filtro de 24 horas a todos os itens coletados
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
