import re
import bs4
import pandas as pd
from tqdm import tqdm
from playwright.sync_api import sync_playwright
from semanticscholar import SemanticScholar
from multiprocessing import Pool, cpu_count
from pdf_utils.pdf_reader import PDFReader


abs_len = 30


def get_abstract_from_semanticscholar(title):
    sch = SemanticScholar(timeout=10, retry=False)
    results = sch.search_paper(title, fields=["title", "abstract"], limit=1)
    if results[0]["abstract"]:
        return re.sub(r"\s+", " ", results[0]["abstract"].strip())
    else:
        return None


def abstract_scraper(url):
    with sync_playwright() as p:
        browser = p.firefox.launch()
        page = browser.new_page()
        page.goto(url, timeout=300000)
        html = page.content()
    html = re.sub("<br>", "\n", html)
    soup = bs4.BeautifulSoup(html, 'html.parser').body
    aria_hidden_elements = soup.find_all(attrs={"aria-hidden": "true"})
    for element in aria_hidden_elements:
        element.decompose()
    res = find_abstract_from_soup(soup)
    return res


def detect_abstract(abstract):
    if len(abstract.text) > abs_len:
        res_abs = abstract
    else:
        next_element = abstract.find_next()
        if next_element and len(next_element.text) > abs_len:
            res_abs = next_element
        else:
            return find_abstract_from_soup(next_element)
    res_abs = re.sub('\s+', ' ', res_abs.text.strip())
    if res_abs[0:8].lower() == 'abstract':
        res_abs = res_abs[8:].strip()
        if res_abs.startswith(':'):
            res_abs = res_abs[1:].strip()
    return res_abs


def find_abstract_from_soup(soup):
    origin_abstract = soup.find_all(class_='abstract')
    if not origin_abstract:
        origin_abstract = soup.find_all(string=lambda text: 'abstract' in text.lower())
    maybe_abstract = []
    for abstract in origin_abstract:
        if type(abstract) == bs4.element.NavigableString or type(abstract) == bs4.element.Tag:
            maybe_abstract.append(detect_abstract(abstract))
    abstract = max(maybe_abstract, key=len, default='')
    return abstract


def find_abstract_from_pdf(fp):
    pr = PDFReader(fp)
    abstract = pr.forward(abstract_only=True)
    return abstract


def process_row(row):
    title = row["title"]
    url = row["pub_url"]
    abstract = None
    try:
        abstract = get_abstract_from_semanticscholar(title)
    except:
        pass
    if not abstract or len(abstract) < abs_len:
        try:
            if url.endswith('.pdf'):
                url = url[:-4]
            else:
                abstract = abstract_scraper(url)
        except:
            pass
    return abstract


def get_abstract_of_scholarly(df):
    if 'abstract' not in df.columns:
        df['abstract'] = None

    rows_to_process = df[df['abstract'].isna()]
    with Pool(cpu_count()) as pool:
        abstracts = list(tqdm(pool.imap(process_row, rows_to_process.to_dict(orient='records')), total=len(rows_to_process)))

    df.loc[df['abstract'].isna(), 'abstract'] = abstracts
    return df


if __name__ == '__main__':
    df = pd.read_csv("summarization_all.csv")
    df = get_abstract_of_scholarly(df)
    df.to_csv("summarization_all.csv", index=False)
