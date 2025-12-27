import requests
from bs4 import BeautifulSoup
import os
import json
import re
import time

BASE_URL = "https://www.gutenberg.org"
START_PAGE = "https://www.gutenberg.org/browse/scores/top"
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_DIR = os.path.join(project_root, "data", "documents")
DATA_DIR = os.path.join(project_root, "data")

def scrape_gutenberg_books(start_url, output_dir, max_documents=40000):
    os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
        print(f"Cleared existing files in {output_dir}")

    visited_urls = set()
    book_urls = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    print(f"Visiting top scores page: {start_url}")
    try:
        response = requests.get(start_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {start_url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    for link in soup.find_all('a', href=True):
        href = link['href']
        if re.match(r"^/ebooks/\d+$", href):
            full_book_url = BASE_URL + href
            if full_book_url not in visited_urls:
                book_urls.append(full_book_url)
                visited_urls.add(full_book_url)
        
        if len(book_urls) >= 100:
            break

    document_count = 0
    for book_url in book_urls:
        if document_count >= max_documents:
            break

        print(f"Processing book page: {book_url}")
        try:
            response = requests.get(book_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {book_url}: {e}")
            time.sleep(1)
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        
        text_link = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            if ".txt" in href and "utf-8" in href and "noimages" in href:
                text_link = href if href.startswith('http') else BASE_URL + href
                break
            elif ".txt" in href and "zip" not in href:
                 text_link = href if href.startswith('http') else BASE_URL + href
                 break
        
        if text_link:
            print(f"Downloading text from: {text_link}")
            try:
                text_response = requests.get(text_link, headers=headers, timeout=10)
                text_response.raise_for_status()
                content = text_response.text

                title_tag = soup.find('h1', property="dcterms:title")
                title = title_tag.get_text(strip=True) if title_tag else "No Title"

                document_data = {
                    "url": text_link,
                    "title": title,
                    "content": content
                }
                
                filename = os.path.join(output_dir, f"doc_{document_count:05d}.json")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(document_data, f, ensure_ascii=False, indent=2)
                document_count += 1

            except requests.exceptions.RequestException as e:
                print(f"Error downloading text from {text_link}: {e}")
        time.sleep(1)

    print(f"Scraping finished. Total documents saved: {document_count}")

if __name__ == "__main__":
    scrape_gutenberg_books(START_PAGE, OUTPUT_DIR, max_documents=40000)
