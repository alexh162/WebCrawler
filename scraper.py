import re
from urllib.parse import urlparse, urljoin, urlunparse
from bs4 import BeautifulSoup
import nltk
import pickle
from nltk.corpus import stopwords
from collections import Counter

# Download and fetch stopwords list
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

# Keep track of the visited URLs
visited_urls = set()

# From assignment 1
def tokenize(page_text_str):
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    total_word_count = 0
    word_frequency = {}
    current_token = ''
    
    for char in page_text_str:   # Iterate through every character in the file
        if char in allowed_chars:  # Append char to token if it's alphanumeric
            current_token += char.lower()   # Convert to lowercase to treat tokens as case-insensitive
        else:   # Non-alphanumeric characters separate the tokens
            if current_token and current_token not in stop_words and len(current_token) > 1:
                total_word_count = total_word_count + 1
                if current_token in word_frequency:
                    word_frequency[current_token] += 1
                else:
                    word_frequency[current_token] = 1
            current_token = ''
    
    if current_token and current_token not in stop_words and len(current_token) > 1:   # Add the last token if it's not empty
        total_word_count = total_word_count + 1
        if current_token in word_frequency:
            word_frequency[current_token] += 1
        else:
            word_frequency[current_token] = 1

    return (total_word_count, word_frequency)

# Merge two maps
def merge_maps(map1, map2):
    counter1 = Counter(map1)
    counter2 = Counter(map2)
    
    merged_counter = counter1 + counter2
    merged_map = dict(merged_counter)
    
    return merged_map

# Fetch the set of visited URLs
def fetchVisited():
    v = set()
    try:
        f = open('visited.pkl', 'rb')
        v = pickle.load(f)
        f.close()
    except:
        pass
    return v

def extract_next_links(url, resp):
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Fetch visited URLs from pkl file
    visited_urls = fetchVisited()
    parsed_url = urlparse(url)
    parsed_no_fragment = parsed_url.scheme + '://' + parsed_url.netloc + parsed_url.path + parsed_url.query

    # Check if valid and not visited
    if resp.status != 200 or parsed_no_fragment in visited_urls or resp.raw_response == None or len(resp.raw_response.content) < 100:
        return list()

    update_statistics(url, resp.raw_response.content)

    # Find all links in the page
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    links = soup.find_all("a", href=True)

    scraped_urls = list()
    for link in links:
        href = link["href"]
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        # if not parsed_href.netloc:
        #     href = urljoin(resp.url, link["href"])
        #     parsed_href = urlparse(href)

        # Remove query and fragment from URL
        stripped_url = urlunparse((parsed_href.scheme, parsed_href.netloc, parsed_href.path, '', '', ''))
        
        # Check if the URL is valid
        if is_valid(stripped_url) and stripped_url not in visited_urls and parsed_href.path.count('/') < 10:
            scraped_urls.append(stripped_url)
    
    visited_urls.add(parsed_no_fragment)
    with open('visited.pkl', 'wb') as file:
        pickle.dump(visited_urls, file)

    return scraped_urls

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|jpg|apk|war|txt|flv|7z|mpg|webm|aac|flac|odc|img|asp|php|cmd|bat|vbs|tif|svg|webp|odt|ods|bam|ppsx"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()) and re.match(
            r'^(\w*.)(ics.uci.edu|cs.uci.edu|stat.uci.edu|informatics.uci.edu)$', parsed.netloc) and not re.match(
            r"/files/pdf/|login.php|/login/|action=login", parsed.path.lower())
    except TypeError:
        print ("TypeError for ", parsed)
        raise

def update_statistics(url, raw_text):
    # Turn raw text to readable text
    soup = BeautifulSoup(raw_text, "html.parser")
    page_text = soup.get_text()

    # Load existing statistics from the file
    existing_stats = {}
    try:
        with open("stats.pkl", 'rb') as file:
            existing_stats = pickle.load(file)
    except FileNotFoundError:
        pass  # File doesn't exist yet or is empty

    # Update unique_pages
    parsed_url = urlparse(url)
    unique_page = parsed_url.scheme + '://' + parsed_url.netloc

    if 'subdomain_map' not in existing_stats:
        existing_stats['subdomain_map'] = {}
    existing_stats['subdomain_map'][unique_page] = existing_stats['subdomain_map'].get(unique_page, 0) + 1

    # Update common words counter
    tokens = tokenize(page_text)
    if "word_dict" not in existing_stats:
        existing_stats["word_dict"] = {}
    existing_stats["word_dict"] = merge_maps(tokens[1], existing_stats["word_dict"])

    # Update page with most words and its URL
    page_words = tokens[0]
    if page_words > existing_stats.get('longest_page_words', 0):
        existing_stats['longest_page_words'] = page_words
        existing_stats['longest_page_url'] = url

    # Save updated statistics back to the file
    with open("stats.pkl", 'wb') as file:
        pickle.dump(existing_stats, file)

def scraper(url, resp):
    links = extract_next_links(url, resp)
    valid_links = [link for link in links if is_valid(link)]
    
    return valid_links