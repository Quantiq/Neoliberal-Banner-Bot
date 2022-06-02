import argparse
import os
import praw
import time
import urllib.request

def main():
    args = arg_parse()
    r = get_reddit_instance()
    r_neoliberal = r.subreddit('Neoliberaltest')

    if args.download:
        create_dir()
        fetch_images(r_neoliberal)
        get_featured_posts(r_neoliberal)
    
    if args.upload:
        upload_to_widget(r_neoliberal)
        upload_to_sidebar(r_neoliberal)
        upload_images(r_neoliberal)

def arg_parse():
    # Parse command-line arguments
    p = argparse.ArgumentParser(description='Simple script to help modify the r/neoliberal featured posts banner.')

    p.add_argument(
        '-d',
        '--download', 
        action='store_true', 
        help='download previous banner images and markdown text'
    )
    p.add_argument(
        '-u', 
        '--upload', 
        action='store_true',
        help='upload new banner images and markdown text'
    )
    return p.parse_args()

def get_reddit_instance():
    # Authentication
    with open('config.txt', 'r') as f:
        lines = f.read().splitlines()

    # Maps config to a dictionary
    config = {key: value for key, value in map(lambda i: i.split('='), lines)}

    print('logging in...')
    reddit = praw.Reddit(
        client_id = config['client_id'],
        client_secret = config['client_secret'],
        password = config['password'],
        user_agent = config['user_agent'],
        username = config['username'],
    )
    print('successful')

    return reddit;

def upload_images(r_neoliberal):
    # Upload images in resources folder to stylesheet
    print('uploading images...')
    directory='./resources'
    for filename in os.listdir(directory):
        if 'header-img-' in filename:
            print(f'uploading {filename}...')
            r_neoliberal.stylesheet.upload(name=filename[:-4], image_path=f'{directory}/{filename}')
            time.sleep(2) # Sleep for 2 seconds because reddit's API throws an error if you try uploading too fast

    # Refreshes the stylesheet. Syntax here is a little bizzare because the PRAW devs decided they wanted to use the
    # same name for all the stylsheet interactions
    print('refreshing stylesheet...')
    ss = r_neoliberal.stylesheet()
    r_neoliberal.stylesheet.update(ss.stylesheet)
    print('successful')

def upload_to_sidebar(r_neoliberal):
    # Delete old featured posts from sidebar and insert markdown from file into the new sidebar
    print('reading markdown...')
    with open('./resources/featured_posts.md', 'r') as f:
        lines_to_insert = f.readlines()

    print('retrieving old sidebar...')
    sidebar = r_neoliberal.wiki['config/sidebar']
    sidebar_lines = sidebar.content_md.splitlines(True)

    # Grab the section of the sidebar responsible for featured posts
    for i, line in enumerate(sidebar_lines):
        if '# Featured Posts' in line:
            start = i + 1
        if '# Announcements' in line:
            end = i

    # modify old featured posts section from the list
    del sidebar_lines[start:end]             # delete old section
    sidebar_lines.insert(start, '\n\n\n')    # insert whitespace

    for line in reversed(lines_to_insert):   # insert featured posts from file
        sidebar_lines.insert(start, line)

    sidebar_lines.insert(start, '\n')        # insert whitespace

    # Upload new sidebar as markdown
    print('uploading new sidebar...')
    sidebar_to_upload = ''.join(sidebar_lines)
    sidebar = r_neoliberal.wiki['config/sidebar']
    sidebar.edit(content=sidebar_to_upload)
    print('successful')

def upload_to_widget(r_neoliberal):
    # Upload featured posts markdown to new.reddit widget
    print('reading markdown...')
    with open('./resources/featured_posts.md') as f:
        markdown = f.read()

    print('uploading to new.reddit...')
    widgets = r_neoliberal.widgets
    for widget in widgets.sidebar:
        if isinstance(widget, praw.models.TextArea):
            if widget.shortName == 'Featured Posts':
                widget.mod.update(text=markdown)
                print('successful')
                break
    
def get_featured_posts(r_neoliberal):
    # Get featured posts as markdown and write to file
    print('retrieving featured posts...')
    widgets = r_neoliberal.widgets
    for widget in widgets.sidebar:
        if isinstance(widget, praw.models.TextArea):
            if widget.shortName == 'Featured Posts':
                markdown = widget.text
                break

    print('writing to file...')
    with open(f'./resources/featured_posts.md', 'w') as f:
        f.write(markdown)
    print('successful')

def fetch_images(r_neoliberal):
    # Fetch featured post images from the subreddit stylesheet
    stylesheet = r_neoliberal.stylesheet()
    images_list = stylesheet.images

    print('retrieving previous banner images...')
    for image in images_list:
        if 'header-img' in image['name']:
            
            img_url = image['url']
            img_name = image['name']
            img_type = image['url'][-3:]

            urllib.request.urlretrieve(img_url, f'./resources/{img_name}.{img_type}')
    print('successful')

def create_dir():
    # Check if resources folder exists. If not, make directory.
    path= './resources'
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == '__main__':
    main()