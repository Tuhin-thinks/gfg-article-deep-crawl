import re
import time
import traceback
from urllib.parse import urlencode, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from check_rank import selenium


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
    url_pre = "http://www.google.com/search?"
    dork_search_query = f"site:news.geeksforgeeks.org {search_query}"

    # search_query = input("Search query: ")
    if not dork_search:
        params = {'q': search_query}
        params.update({'start': page_count * 10})
    else:
        params = {'q': dork_search_query}
    quoted_query = urlencode(params)

    url = url_pre + quoted_query
    print(url)
    # check page for the url
    selenium.init_driver().get(url)
    has_more_results = selenium.check_has_more_contents()
    # if no more results available, do a dork search
    if not has_more_results and not dork_search:
        # last search was normal search and there are no more pages to be
        # searched, thus do a dork search and return the results.
        print(f"[No more articles available at page: {page_count}, "
              f"starting dork search]")
        (rank, higher_ranking_articles,
         search_status) = do_search(search_query=search_query,
                                    target_url=target_url,
                                    dork_search=True)
        if search_status != "NF":
            search_status = "NR"
        return rank, higher_ranking_articles, search_status
    elif not has_more_results and dork_search:
        # if current search is a dork search and no more results available,
        # then return the status as not found
        return "Not Found", "", "NF"

    # titles, search_links = get_search_links(soup)
    # call the selenium scraper from here
    titles, search_links = selenium.get_search_links_selenium(url)

    for rank, (title, link) in enumerate(zip(titles, search_links), 1):
        domain = get_domain(link)
        if domain == "news.geeksforgeeks.org" and Url(link) == Url(target_url):

            if rank > 1:
                print(f"[Ranking 1-{rank - 1} articles]")
                print("\n".join(search_links[:rank - 1]))
            print(f"\n{16 * '--'}\n")
            higher_ranking_articles = "\n".join(search_links[:rank - 1])

            return (rank + page_count * 10,
                    higher_ranking_articles, "")

    if not dork_search and page_count >= 10:
        # previously was doing normal search,
        # but in 10 pages the target no found
        # so, now try with dork search
        (rank, higher_ranking_articles,
         search_status) = do_search(search_query=search_query,
                                    target_url=target_url,
                                    dork_search=True)
        if search_status != "NF":
            search_status = "NR"
        return rank, higher_ranking_articles, search_status
    elif not dork_search and page_count < 10:
        # previously was trying normal search, and in the last page the target
        # is not found, so try to go to the next page and try a normal search
        (rank, higher_ranking_articles,
         search_status) = do_search(search_query, target_url,
                                    dork_search=False,
                                    page_count=page_count + 1)
        return rank, higher_ranking_articles, search_status

    # if the search was a dork search and no match found,
    # so return the status of not found
    return "Not Found", "", "NF"


def main(inp_csv_path: str, out_csv_path: str, modify_existing: bool = False,
         start_from: int = 0):
    if modify_existing:
        topic_df = load_csv_data(out_csv_path)
    else:
        topic_df = load_csv_data(inp_csv_path)
    all_cols = ["Rank", "Higher Ranking Articles", "Search Status"]
    if not modify_existing:
        for col_name in all_cols:
            topic_df[col_name] = None

    index = 0
    try:
        if len(topic_df) <= start_from:
            print("All data already scraped. "
                  "Delete config file to start from the beginning.")
            return
        for index, row in topic_df.iloc[start_from:].iterrows():
            topic_str = row['Title']
            target_url = row['Link']
            (rank, higher_ranking_articles,
             deep_search_status) = do_search(topic_str, target_url=target_url,
                                             dork_search=False)
            topic_df.loc[index, all_cols] = [rank,
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
    return index


if __name__ == '__main__':
    main()
