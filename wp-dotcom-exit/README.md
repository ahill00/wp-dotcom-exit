wp-dotcom-exit
===

I used this script to post an announcement that I am leaving my site at wordpress.com, and will ultimately use it clear all content and just post links directly to my new site.

wordpress.com provides XML exports of content, but that's not a complete migration strategy for a 15 year old website that needs to change its URL.

wp-dotcom-exit requires python 3.11 and poetry.  I heavily leveraged ChatGPT to make this script. 

wordpress.com APIs requires creating a Client Application and secrets. See [Wordpress.com API docs for more info](https://developer.wordpress.com/docs/api/getting-started/). 

This script requires these environment variables:
* `WP_API_KEY`
* `WP_CLIENT_ID`

There's also a command line argument `--blog-id` which is a numeric identifier for the specific wordpress.com blog you're updating. I got my blog ID from [this post](https://wordpress.com/forums/topic/how-to-find-blog-id/) on the support forums.


See this post for more details about exiting Wordpress.com.
