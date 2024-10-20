import re
import time

from scholarly import scholarly
import pandas as pd
from tqdm import tqdm


def get_scholar(keyword, year_low=None, year_high=None):
    scholarly.set_timeout(100)
    searched_scholar = scholarly.search_pubs(query=keyword, year_low=year_low, year_high=year_high)
    papers = []
    count = 1
    for i in tqdm(searched_scholar):
        title = i['bib']['title']
        if title.startswith("\"") and title.endswith("\""):
            title = title[1:-1]
        # try:
        #     bib = scholarly.bibtex(i)
        # except:
        #     bib = None
        papers.append([title.strip(), i['bib']['pub_year'], i['num_citations'], None,
                       i.get('pub_url', None),
                       i.get('url_scholarbib', None),
                       i.get('citedby_url', None)
                       ])
        if count % 10 == 0:
            time.sleep(0.08)
        count += 1
    papers_df = pd.DataFrame(papers, columns=["title", "pub_year", "num_citations", "bib", "pub_url", "bib_url", "citedby_url"])
    papers_df.drop_duplicates(subset=['title'], inplace=True)
    return papers_df


def check_arxiv(df: pd.DataFrame):
    for i in tqdm(range(len(df))):
        if "arxiv" in df["pub_url"][i]:
            pass


if __name__ == '__main__':
    keyword = "summarization gpt"

    papers_df = get_scholar(keyword, year_low=2022)
    keyword = re.sub(r"\s", "_", keyword)
    papers_df.to_csv(f"{keyword}_all.csv", index=False)