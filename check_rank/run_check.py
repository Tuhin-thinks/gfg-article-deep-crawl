import re
import time
import traceback
from urllib.parse import urlencode, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .tools import Url

__wait = True
INPUT_CSV_PATH = "topic_list.csv"
OUTPUT_CSV_PATH = "Ranking_Results.csv"
WAIT_TIME_SECS = 0


def get_domain(link: str):
    return urlparse(link).hostname


def check_more_results_available(soup: BeautifulSoup) -> bool:
    no_more_contents_text_p_selector = 'div.card-section>p'
    p_tag = soup.select_one(no_more_contents_text_p_selector)
    if p_tag:
        p_text = p_tag.text
        match = re.search('your search.*did not match any documents.*', p_text,
                          re.I)
        if match:
            return False
    else:
        return True


def load_csv_data(file_path) -> pd.DataFrame:
    topics_df = pd.read_csv(file_path)
    return topics_df


def get_search_links(soup):
    divs = soup.find_all('div')
    links = []
    titles = []

    for div in divs:
        link = div.find('a')
        if link:
            link_mod = link[
                'href']  # getting only the hyperlink portion of the attribute
            try:
                if link_mod[
                   link_mod.index('=') + 1:link_mod.index('&')
                   ].startswith('https://'):
                    link_ = link_mod[link_mod.index('=') + 1:
                                     link_mod.index('&')]
                    if link_ not in links and "support.google.com" not in link_:
                        try:
                            h3 = link.find_next("h3").text
                            titles.append(h3)
                            links.append(link_)
                        except AttributeError:
                            # print(link_)
                            continue
            except ValueError:
                pass
    return titles, links


def do_search(search_query: str, target_url: str, dork_search: bool,
              page_count: int = 0):
    """
    This will do a Google search and return the ranking of any gfg article
    and along with the last improved status
    :param search_query: String to
    :param target_url:
    :param dork_search:
    :param page_count:
    search in google
    """
    url_pre = "https://www.google.com/search?"
    dork_search_query = f"site:news.geeksforgeeks.org {search_query}"

    # search_query = input("Search query: ")
    params = {'q': search_query}
    if not dork_search:
        params.update({'start': page_count * 10})
    quoted_query = urlencode(params)

    url = url_pre + quoted_query
    print(url)

    response = requests.get(url)

    with open("search-page.html", 'wb') as file:
        file.write(response.content)

    soup = BeautifulSoup(response.content, 'html5lib')

    has_more_results = check_more_results_available(soup)
    # if no more results available, do a dork search
    if not has_more_results:
        print(f"[No more articles available at page: {page_count}, "
              f"starting dork search]")
        (rank, gfg_article_info, higher_ranking_articles,
         search_status) = do_search(search_query=dork_search_query,
                                    target_url=target_url,
                                    dork_search=True)
        if search_status != "NF":
            search_status = "NR"
        return rank, gfg_article_info, higher_ranking_articles, search_status

    titles, search_links = get_search_links(soup)

    for rank, (title, link) in enumerate(zip(titles, search_links), 1):
        domain = get_domain(link)
        if domain == "news.geeksforgeeks.org" and Url(link) == Url(target_url):

            if rank > 1:
                print(f"[Ranking 1-{rank - 1} articles]")
                print("\n".join(search_links[:rank - 1]))
            print(f"\n{16 * '--'}\n")
            gfg_article_info = f"{link}"
            higher_ranking_articles = "\n".join(search_links[:rank - 1])

            return (rank + page_count * 10, gfg_article_info,
                    higher_ranking_articles, "")

    if not dork_search and page_count >= 10:
        (rank, gfg_article_info, higher_ranking_articles,
         search_status) = do_search(search_query=dork_search_query,
                                    target_url=target_url,
                                    dork_search=True)
        if search_status != "NF":
            search_status = "NR"
        return rank, gfg_article_info, higher_ranking_articles, search_status
    elif not dork_search and page_count < 10:
        (rank, gfg_article_info, higher_ranking_articles,
         search_status) = do_search(search_query, target_url,
                                    dork_search=False,
                                    page_count=page_count + 1)
        return rank, gfg_article_info, higher_ranking_articles, search_status
    return "Not Found", '', "", "NF"


def main(inp_csv_path: str, out_csv_path: str):
    topic_df = load_csv_data(inp_csv_path)
    all_cols = ["Rank", "GFG Article INFO", "Higher Ranking Articles",
                "Search Status"]
    for col_name in all_cols:
        topic_df[col_name] = None

    index = 0
    try:
        for index, row in topic_df.iterrows():
            topic_str = row['Title']
            target_url = row['Link']
            (rank, gfg_article_info, higher_ranking_articles,
             deep_search_status) = do_search(topic_str, target_url=target_url,
                                             dork_search=False)
            topic_df.loc[index, all_cols] = [rank,
                                             gfg_article_info,
                                             higher_ranking_articles,
                                             deep_search_status]

            if __wait:
                print(f"waiting {WAIT_TIME_SECS} secs.")
                time.sleep(WAIT_TIME_SECS)
    except Exception as e:
        print(f"Search stopped at index: {index}, due to error: {e.__str__()}")
        traceback.print_exc()
    except KeyboardInterrupt:
        print(f"Script stopped manually at index: {index}. "
              f"Saving modified dataframe to csv: {out_csv_path}.")

    # write the dataframe to output csv file
    topic_df.to_csv(out_csv_path, index=False)


if __name__ == '__main__':
    main()
