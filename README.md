# [Retrieve Papers](https://github.com/JinHanLei/RetrievePapers/upload/main)

Code for our paper "A Comprehensive Survey on Automatic Text Summarization with Exploration of LLM-Based Methods". The literature collection process includes:

1. Comprehensive Collection: Utilizing a web crawler with synonym-replaced keywords to extensively scrape relevant papers in the field of ATS. ([get_scholar.py](get_scholar.py))
2. Relevance Filtering: Scraping additional abstracts and filtering out papers that are irrelevant to ATS. ( [get_abstract_by_playwright.py](get_abstract_by_playwright.py))
3. Categorization: Classifying each paper using prompt engineering and few-shot learning with LLMs. ( [classify_papers.py](classify_papers.py) )