import requests
import urllib.request
import xml.etree.ElementTree as ET
import datetime
import html
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
import time

def clean_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()

def get_original_url(url: str) -> str:
    """Retorna a URL original, pois não estamos mais usando o Google News para redirecionamento."""
    return url

def fetch_full_article(url: str) -> str:
    """Busca o conteúdo completo do corpo da matéria, sem título, URL ou nome do site."""
    try:
        # Adiciona timeout e user-agent para evitar bloqueios
        req = urllib.request.Request(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
        
        # Remove elementos desnecessários primeiro
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<nav[^>]*>.*?</nav>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<header[^>]*>.*?</header>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<footer[^>]*>.*?</footer>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<aside[^>]*>.*?</aside>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<div[^>]*class="[^\"]*sidebar[^\"]*"[^>]*>.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<div[^>]*class="[^\"]*menu[^\"]*"[^>]*>.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<div[^>]*class="[^\"]*ad[^\"]*"[^>]*>.*?</div>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Busca por padrões mais específicos de conteúdo de artigo/matéria
        article_patterns = [
            r'<div[^>]*class="[^\"]*entry-content[^\"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^\"]*post-content[^\"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^\"]*article-body[^\"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^\"]*story-body[^\"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^\"]*content-body[^\"]*"[^>]*>(.*?)</div>',
            r'<section[^>]*class="[^\"]*article-content[^\"]*"[^>]*>(.*?)</section>',
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^\"]*text[^\"]*"[^>]*>(.*?)</div>',
            r'<main[^>]*>(.*?)</main>',
        ]
        
        content = ""
        for pattern in article_patterns:
            matches = re.findall(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
            if matches:
                # Pega o maior match (provavelmente o conteúdo principal)
                content = max(matches, key=len)
                break
        
        # Se não encontrou padrões específicos, busca por parágrafos na página
        if not content:
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_content, flags=re.DOTALL | re.IGNORECASE)
            if paragraphs:
                # Filtra parágrafos muito curtos (provavelmente não são conteúdo principal)
                main_paragraphs = [p for p in paragraphs if len(clean_html(p)) > 50]
                if main_paragraphs:
                    content = ' '.join(main_paragraphs)
        
        if not content:
            return "Conteúdo não disponível"
        
        # Limpa o HTML e remove elementos indesejados do texto
        clean_content = clean_html(content)
        
        # Remove linhas que parecem ser título, URL, nome do site, etc.
        lines = clean_content.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip linhas muito curtas (provavelmente não são conteúdo)
            if len(line) < 20:
                continue
                
            # Skip linhas que parecem ser metadados
            if any(keyword in line.lower() for keyword in [
                'compartilh', 'share', 'twitter', 'facebook', 'instagram',
                'por:', 'by:', 'fonte:', 'source:', 'publicado', 'published',
                'atualizado', 'updated', 'tags:', 'categoria:', 'category:',
                'leia mais', 'read more', 'clique aqui', 'click here',
                'assine', 'subscribe', 'newsletter', 'comments', 'comentários'
            ]):
                continue
                
            # Skip linhas que são principalmente URLs ou emails
            if re.search(r'https?://|www\.|@.*\.com', line):
                continue
                
            filtered_lines.append(line)
        
        # Junta as linhas filtradas
        final_content = '\n\n'.join(filtered_lines)
        
        # Remove excesso de espaços em branco
        final_content = re.sub(r'\n{3,}', '\n\n', final_content)
        final_content = re.sub(r' {2,}', ' ', final_content)
        
        # Limita a 2300 caracteres
        if len(final_content) > 2300:
            final_content = final_content[:2297] + "..."
        
        return final_content.strip() if final_content.strip() else "Conteúdo não disponível"
        
    except Exception as e:
        print(f"Erro ao buscar artigo {url}: {e}")
        return "Conteúdo não disponível"

def escape_xml(text: str) -> str:
    """Escapa caracteres especiais para XML, incluindo & em URLs."""
    if not text:
        return ""
    # Usar html.escape com quote=True para escapar aspas também
    return html.escape(text, quote=True)

def build_feed_url(lang: str) -> str:
    """Retorna a URL do RSS com base no idioma."""
    if lang == "en-ai-news":
        return "https://www.artificialintelligence-news.com/feed/"
    elif lang == "en-wired":
        return "https://www.wired.com/feed/tag/ai/latest/rss"
    else:
        raise ValueError("Idioma não suportado")

def fetch_items(feed_url: str):
    print(f"Buscando feed: {feed_url}")
    try:
        with urllib.request.urlopen(feed_url, timeout=15) as response:
            data = response.read()
    except Exception as e:
        print(f"Erro ao abrir URL do feed {feed_url}: {e}")
        return []

    root = ET.fromstring(data)
    items = []
    
    for item_elem in root.findall(".//item"):
        title = item_elem.findtext("title", default="")
        link = item_elem.findtext("link", default="")
        description = item_elem.findtext("description", default="")
        pub_date_str = item_elem.findtext("pubDate")
        
        # Tenta obter a data de publicação
        pub_date = None
        if pub_date_str:
            try:
                pub_date = parsedate_to_datetime(pub_date_str).astimezone(datetime.timezone.utc)
            except Exception:
                pass
        
        # Se a data de publicação não foi encontrada ou é inválida, usa a data atual
        if not pub_date:
            pub_date = datetime.datetime.now(datetime.timezone.utc)
        
        # Para os novos feeds, o link já é a URL original
        original_url = link
        
        # Busca o conteúdo completo do artigo usando a URL original
        print(f"Buscando conteúdo de: {title[:50]}...")
        full_content = fetch_full_article(original_url)
        
        # Se não conseguiu buscar o conteúdo completo, usa a descrição original limpa
        final_description = full_content if full_content != "Conteúdo não disponível" else clean_html(description)
        
        items.append({
            "title": title,
            "link": link, 
            "original_url": original_url, 
            "description": final_description,
            "pubDate": pub_date,
        })
        
        # Adiciona uma pequena pausa para não sobrecarregar os servidores
        time.sleep(1.0)
        
    return items

def filter_last_7_days(items):
    """Filtra itens dos últimos 7 dias."""
    now = datetime.datetime.now(datetime.timezone.utc)
    seven_days = datetime.timedelta(days=7)
    return [item for item in items if now - item["pubDate"] <= seven_days]

def generate_combined_rss():
    feeds = ["en-ai-news", "en-wired"]
    all_items = []
    
    for feed in feeds:
        url = build_feed_url(feed)
        fetched = fetch_items(url)
        filtered = filter_last_7_days(fetched)
        all_items.extend(filtered)
    
    # Ordena por data de publicação (mais recente primeiro)
    all_items.sort(key=lambda x: x["pubDate"], reverse=True)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<rss version=\"2.0\">",
        "  <channel>",
        "    <title>Notícias de Inteligência Artificial (EN)</title>",
        "    <link>https://github.com/rafaelamiranda/noticias-ia</link>",
        "    <description>",
        "Principais notícias relacionadas a inteligência artificial",
        "dos últimos 7 dias, em Inglês.",
        "    </description>",
        f"    <lastBuildDate>{now.strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>",
    ]
    
    for item in all_items:
        lines.extend([
            "    <item>",
            f"      <title>{escape_xml(item['title'])}</title>",
            f"      <link>{escape_xml(item['link'])}</link>",
            f"      <description>{escape_xml(item['description'])}</description>",
            f"      <pubDate>{item['pubDate'].strftime('%a, %d %b %Y %H:%M:%S GMT')}</pubDate>",
            f"      <guid>{escape_xml(item['original_url'])}</guid>",
            "    </item>",
        ])
    
    lines.extend(["  </channel>", "</rss>"])
    
    filename = "index.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"RSS combinado gerado: {filename}")

if __name__ == "__main__":
    generate_combined_rss()