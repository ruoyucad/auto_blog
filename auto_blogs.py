import requests
import feedparser
from openai import OpenAI
import shopify
import json
import random
from datetime import datetime

# Configure your Shopify credentials
SHOP_NAME = os.getenv('SHOP_NAME')
ADMIN_API_ACCESS_TOKEN =  os.getenv('ADMIN_API_ACCESS_TOKEN') # Your Admin API access token
# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

# List of RSS feeds for movies and anime
RSS_FEEDS = [
    'https://www.animenewsnetwork.com/news/rss.xml',
    'https://rss.nytimes.com/services/xml/rss/nyt/Movies.xml',
    'https://www.cinemablend.com/rss/topic/news/movies',
    'https://www.ign.com/feeds/anime.rss',
    'https://www.slashfilm.com/feed/',
    'https://www.avclub.com/rss',
    'https://screenrant.com/feed/'
]

# Set up Shopify session
shop_url = f"https://{SHOP_NAME}.myshopify.com/admin"
session = shopify.Session(shop_url, version="2023-01", token=PASSWORD)
shopify.ShopifyResource.activate_session(session)

# Fetch latest news from RSS feeds
def fetch_latest_news():
    articles = []
    for feed in RSS_FEEDS:
        parsed_feed = feedparser.parse(feed)
        for entry in parsed_feed.entries[:5]:  # Fetch the top 5 articles from each feed
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary,
                'published': entry.published,
                'source': feed
            })
    # Sort articles by published date and return the latest one
    articles.sort(key=lambda x: x['published'], reverse=True)
    return articles

# Generate a catchy and controversial review using OpenAI
def generate_review(title, summary):
    openai.api_key = OPENAI_API_KEY
    prompt = (f"Write a catchy, controversial, and SEO-friendly review with emojis for the following article to persuade "
              f"people to buy cosplay costumes. The review should be engaging and include a call to action to "
              f"buy costumes from our store.\n\nTitle: {title}\nSummary: {summary}")
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a marketing copywriter who loves using emojis."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    review = response.choices[0].message['content'].strip()
    return review

# Get the blog ID for the "news" blog
def get_news_blog_id():
    try:
        blogs = shopify.Blog.find()
        for blog in blogs:
            if blog.title.lower() == 'news':
                return blog.id
        raise Exception('News blog not found')
    except Exception as e:
        print(f"Error fetching blogs: {e}")
        raise

# Create a blog post on Shopify
def create_blog_post(title, content, blog_id):
    try:
        new_article = shopify.Article()
        new_article.blog_id = blog_id
        new_article.title = title
        new_article.body_html = content
        new_article.save()

        if new_article.errors:
            print(f'Failed to create blog post: {new_article.errors.full_messages()}')
        else:
            print('Blog post created successfully')
    except Exception as e:
        print(f"Error creating blog post: {e}")

# Ensure content uniqueness
def check_existing_posts(title):
    try:
        articles = shopify.Article.find()
        for article in articles:
            if article.title == title:
                return True
        return False
    except Exception as e:
        print(f"Error checking existing posts: {e}")
        return False

# Main function to automate the process
def main():
    articles = fetch_latest_news()
    news_blog_id = get_news_blog_id()
    for article in articles:
        if not check_existing_posts(article['title']):
            review = generate_review(article['title'], article['summary'])
            content = f"<p>{review}</p><p>Check out our exclusive <a href='https://abccoser.com/collections/all'>cosplay costumes</a>! 🎭👗</p>"
            create_blog_post(article['title'], content, news_blog_id)
            break  # Only post one article per run

if __name__ == "__main__":
    main()
