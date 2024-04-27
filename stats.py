import pickle
from collections import Counter

def print_stats():
    try:
        with open("visited.pkl", 'rb') as file:
            visited_urls = pickle.load(file)
            print(f"How many unique pages did you find?\n{len(visited_urls)}\n")
            
        with open("stats.pkl", 'rb') as file:
            existing_stats = pickle.load(file)

            unique_pages = existing_stats.get('subdomain_map', {})

            print("Unique Pages Map:")
            if unique_pages:
                for word in sorted(unique_pages.keys()):
                    count = unique_pages[word]
                    print(f"{word}, {count}")
            print()

            print("Longest Page URL:")
            print(existing_stats.get('longest_page_url', 'Not found'))
            print()

            print("Longest Page Words:")
            print(existing_stats.get('longest_page_words', 0))
            print()

            # Print the 50 most common words
            print("Top 50 Most Common Words:")
            word_dict = existing_stats.get('word_dict', {})
            if word_dict:
                common_words_counter = Counter(word_dict)
                top_50_words = common_words_counter.most_common(50)
                for word, count in top_50_words:
                    print(f"{word}: {count}", end=', ')
            print()
    except FileNotFoundError:
        print("No statistics found. Run 'update_statistics' function first.")

print_stats()
