import os
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

def get_html_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.html')]

def extract_links(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    links = []
    # Identify project links - usually in card-body or glass-btn
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'github.com' in href or 'public.tableau.com' in href:
            # Try to find the project title
            card = a.find_parent('div', class_='card-body')
            title = "Unknown"
            if card:
                title_tag = card.find(['h4', 'h3'])
                if title_tag:
                    title = title_tag.get_text(strip=True)
            links.append({'file': os.path.basename(html_file), 'title': title, 'url': href})
    return links

def verify_link(link_info):
    url = link_info['url']
    try:
        # Use a real user-agent to avoid being blocked
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        
        # GitHub might return 404 for private or non-existent, 200/301 for public
        if response.status_code == 200:
            return {**link_info, 'status': 'OK'}
        elif response.status_code == 404:
            return {**link_info, 'status': 'FAILED (404)'}
        else:
            # Some sites might block HEAD requests, try GET
            response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                return {**link_info, 'status': 'OK'}
            else:
                return {**link_info, 'status': f'FAILED ({response.status_code})'}
    except Exception as e:
        return {**link_info, 'status': f'ERROR ({str(e)})'}

def main():
    root_dir = '/Users/sayamkumar/Desktop/My-Portfolio-Website'
    html_files = get_html_files(root_dir)
    all_links = []
    
    for f in html_files:
        all_links.extend(extract_links(f))
    
    # Run verification in parallel
    print(f"Verifying {len(all_links)} links...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(verify_link, all_links))
    
    # Print results
    failed_links = [r for r in results if r['status'] != 'OK']
    print("\n--- FAILING LINKS ---")
    for r in failed_links:
        print(f"[{r['status']}] File: {r['file']} | Project: {r['title']} | URL: {r['url']}")
    
    print(f"\nTotal Links: {len(all_links)}")
    print(f"Passed: {len(all_links) - len(failed_links)}")
    print(f"Failed: {len(failed_links)}")

if __name__ == "__main__":
    main()
