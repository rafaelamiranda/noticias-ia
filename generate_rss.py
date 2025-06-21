import requests
from bs4 import BeautifulSoup
import datetime

def generate_rss():
    # Lógica para buscar as notícias (exemplo simplificado)
    # Você pode adaptar o código que usamos anteriormente para buscar de várias fontes
    news_items = [
        {
            'title': 'Exemplo de Notícia 1',
            'link': 'https://example.com/news1',
            'description': 'Descrição da notícia 1.'
        },
        {
            'title': 'Exemplo de Notícia 2',
            'link': 'https://example.com/news2',
            'description': 'Descrição da notícia 2.'
        }
    ]

    rss_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss_content += '<rss version="2.0">\n'
    rss_content += '<channel>\n'
    rss_content += '<title>Notícias de Inteligência Artificial</title>\n'
    rss_content += '<link>https://noticias-ia.pages.dev</link>\n' # URL do seu site
    rss_content += '<description>Últimas notícias sobre IA.</description>\n'
    rss_content += f'<lastBuildDate>{datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>\n'

    for item in news_items:
        rss_content += '<item>\n'
        rss_content += f'<title>{item["title"]}</title>\n'
        rss_content += f'<link>{item["link"]}</link>\n'
        rss_content += f'<description>{item["description"]}</description>\n'
        rss_content += f'<pubDate>{datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</pubDate>\n'
        rss_content += f'<guid>{item["link"]}</guid>\n'
        rss_content += '</item>\n'

    rss_content += '</channel>\n'
    rss_content += '</rss>\n'

    with open('index.xml', 'w', encoding='utf-8') as f:
        f.write(rss_content)

if __name__ == '__main__':
    generate_rss()