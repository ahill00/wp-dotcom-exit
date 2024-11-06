import os
import requests
import webbrowser
import argparse
import json
from dateutil.parser import isoparse 

# WordPress OAuth2 credentials
CLIENT_ID = os.getenv('WP_CLIENT_ID')
CLIENT_SECRET = os.getenv('WP_API_KEY')  # Fetching client secret from the environment variable
REDIRECT_URI = 'https://dev.ahill.net'  # Must match the redirect URI in your app settings
AUTH_URL = 'https://public-api.wordpress.com/oauth2/authorize'
TOKEN_URL = 'https://public-api.wordpress.com/oauth2/token'
NEW_DOMAIN = 'https://dev.ahill.net'
ANNOUNCEMENT = '<h2>Announcement</h2><p>This site is moving from virtualandy.wordpress.com to dev.ahill.net. All content is available on dev.ahill.net. virtualandy.wordpress.com content will not be available at this URL in 2025.</p><h2>Original Post</h2>'

# Step 1: Direct the user to the authorization URL to get the authorization code
def get_authorization_code():
    auth_request_url = (
        f'{AUTH_URL}?client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}&response_type=code'
    )
    print(f'Please go to this URL and authorize access: {auth_request_url}')
    webbrowser.open(auth_request_url)
    
    # The user will get redirected to your redirect URI with a code parameter.
    # You can manually enter the code here after authorization.
    code = input('Enter the authorization code from the URL: ')
    return code

# Step 2: Exchange the authorization code for an access token
def get_access_token(authorization_code):
    data = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'client_secret': CLIENT_SECRET,  # Use the client secret from the environment variable
        'code': authorization_code,
        'grant_type': 'authorization_code'
    }

    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        token_info = response.json()
        return token_info['access_token']
    else:
        print(f'Error retrieving access token: {response.status_code}, {response.text}')
        return None

# Step 3: Use the access token to make authenticated requests
def get_posts(access_token, blog_id):
    next_page = None
    posts, next_page = _page_of_posts(access_token, blog_id, next_page)
    while next_page:
        p, next_page = _page_of_posts(access_token, blog_id, next_page)
        posts += p
    return posts

def _page_of_posts(access_token, blog_id, page_handle):
    posts_url = f'https://public-api.wordpress.com/rest/v1.1/sites/{blog_id}/posts'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    posts = []
    next_page = None
    query_params = {}
    query_params.update({'page_handle': page_handle})
    response = requests.get(posts_url, params=query_params, headers=headers)
    if response.status_code == 200:
        posts = response.json().get('posts', [])
        meta = response.json().get('meta')
        if meta:
            next_page = meta.get('next_page')
    else:
        print(f"Failed to retrieve posts: {response.status_code}, {response.text}")
    return posts, next_page

def update_post(access_token, blog_id, post_id, updated_content, commit):
    if not commit:
        print(f"DRY RUN: Would update post {post_id} with new content.")
        return
    
    update_url = f'https://public-api.wordpress.com/rest/v1.1/sites/{blog_id}/posts/{post_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'content': updated_content
    }
    
    response = requests.post(update_url, headers=headers, data=data)
    if response.status_code == 200:
        print(f"Post {post_id} updated successfully.")
    else:
        print(f"Failed to update post {post_id}: {response.status_code}, {response.text}")

def append_link_to_content(post, clear_content, commit):
    """Generate a new link with the same year/month/day/slug and place it at the top of the post content, optionally clearing the original content."""
    slug = post['slug']
    date_str = post['date']  # Example: '2023-09-29T10:45:00'
    
    # Convert the date string into a datetime object
    post_date = isoparse(date_str)
    
    # Extract year, month, and day
    year = post_date.strftime('%Y')
    month = post_date.strftime('%m')
    day = post_date.strftime('%d')
    
    # Construct the new link with year/month/day/slug
    new_link = f'<p><a href="{NEW_DOMAIN}/{year}/{month}/{day}/{slug}">This content has moved to: {NEW_DOMAIN}/{year}/{month}/{day}/{slug}</a>, and will not be available at this URL in 2025.</p>'
    
    # Get the original content of the post
    original_content = post['content']
    
    # If the link is already in the post, don't modify the content
    if new_link in original_content:
        print(f"Link already present in post: {post['title']}")
        return original_content  # Return the content without changes
    
    # Prepare the new content: Blurb + Link
    new_content_top = f'{ANNOUNCEMENT}<p>{new_link}</p>'
    
    if clear_content:
        # If clear_content is True, only use the new content
        updated_content = new_content_top
    else:
        # Otherwise, prepend the new content to the original post content
        updated_content = new_content_top + original_content
    
    return updated_content

def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Append links to WordPress posts with optional dry-run and content-clearing features.")
    
    # Optional arguments
    parser.add_argument('--commit', action='store_true', help="Make actual changes to the posts. Default is dry-run mode.")
    parser.add_argument('--clear-content', action='store_true', help="Clear the post content and only keep the new link and blurb at the top.")
    parser.add_argument('--blog-id', required=True, help="WordPress blog ID.")
    
    args = parser.parse_args()
    
    # Step 1: Get authorization code
    auth_code = get_authorization_code()
    
    # Step 2: Exchange authorization code for access token
    access_token = get_access_token(auth_code)
    
    if access_token:
        # Step 3: Fetch all posts and update them
        posts = get_posts(access_token, args.blog_id)
        modified_count = 0

        for post in posts:
            post_id = post['ID']
            print(f"Processing post: {post['title']}")
            
            # Append the link with the correct year/month/day/slug format to the content
            updated_content = append_link_to_content(post, args.clear_content, args.commit)
            
            if updated_content != post['content']:
                modified_count += 1
                update_post(access_token, args.blog_id, post_id, updated_content, args.commit)
        
        print(f"Total posts modified: {modified_count}")
        if not args.commit:
            print("Dry run complete. No actual changes were made.")

if __name__ == '__main__':
    main()
