import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import hashlib
import re

import promptlayer
openai = promptlayer.openai

# TODO: This should be in an env and per user
promptlayer.api_key = "pl_2165376193707c1ecd2b9044bfee557c"
openai.api_key = "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"


###########################
# Identifier prompts
# Tells if you if should run a page prompt on a page

url_is_ecommerce_item_prompt = """Please tell me if the following page URL is the page for an ecommerce item. 

If it is, please print YES.
If it is not, please print NO.
If you are unsure, please print UNSURE

Page URL: {page_url}
Output:
"""

url_is_case_study_prompt = """Please tell me if the following page URL is the page that has a case study or is highly likely to have a case study. 

If it is, please print YES.
If it is not, please print NO.
If you are unsure, please print UNSURE

Page URL: {page_url}
Output:
"""

###########################
# Page prompts
# Runs prompt on cleaned HTML to get data
# cleaned HTML is HTML that only has content. Ie code, random cruft is removed to save tokens


scrape_ecommerce_data_page_prompt = """
"""

def run_prompt_on_page_content(cleaned_content, page_prompt):
    pass

def call_inference(model, prompt, pl_tags):
    # models = 'gpt-4', 'gpt-3.5-turbo'

    messages = [{'role': 'user', 'content': prompt}]

    completion = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        # stream=True,
        pl_tags=pl_tags,
        temperature=0,
        max_tokens=2048,
    )

    content = completion.choices[0]['message'].content

    return content

def classify_page(url, url_prompt):
    classification = call_inference("gpt-3.5-turbo", url_prompt.format(page_url=url), ["Saleh", "Crawler Test"])

    return classification

def clean_url_to_filename(url):
    return re.sub(r'\W+', '_', url)

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def clean_HTML(html):
    pass
    # TODO: do a document.body.textContent + remove JS, random shit that doesn't matter
    # That way we can limit the tokens to pass to an LLM

def get_all_website_links(url):
    urls = set()
    domain_name = urlparse(url).netloc

    soup = BeautifulSoup(requests.get(url).content, "html.parser")

    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            continue
        if href in internal_urls:
            continue
        
        # Classification step. If the URL looks like something you want, scrape
        if domain_name in url:
            print(f"Internal link: {href}")
            urls.add(href)
            internal_urls.add(href)

            page_content = requests.get(href).text
            save_page_content(href, page_content)
            # Save raw page content

            # TODO: run prompt if the page is the right type of page
            # ie if page is relevant
            # TODO: what if I want to run multiple prompts per page? 
            # like case study prompt on a case study page, ecommerce data on ecommerce page, etc.
            # Maybe the move is to define a JSON with types? 
            # TODO: Need to also parse the outputs to make sure they are the right type
            if classify_page(href, url_is_ecommerce_item_prompt) == "YES":
                print("=========", href)
                # cleaned_html = "..." #TODO: extract the content part of HTML, exclude code etc
                # run_prompt_on_page_content(cleaned_content, page_prompt)
                pass

            continue
        else:
            # This isn't really doing anything tbh....
            # print(f"External link: {href}")
            external_urls.add(href)
            continue

    return urls

internal_urls = set()
external_urls = set()
all_urls = {}

total_urls_visited = 0
max_urls_to_visit = 500

def crawl(url, max_urls=50):
    global total_urls_visited
    total_urls_visited += 1
    links = get_all_website_links(url)
    for link in links:
        if total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)

def save_page_content(url, html_content):
    #url_hash = hash(url)
    url_hash = clean_url_to_filename(url)
    all_urls[url] = f"{url_hash}.txt"
    with open(f"{url_hash}.txt", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    url = "https://www.target.com/"
    crawl(url, max_urls=max_urls_to_visit)
    for internal_url in internal_urls:
        page_content = requests.get(internal_url).text
        save_page_content(internal_url, page_content)
    print("All URLs: ", all_urls)
