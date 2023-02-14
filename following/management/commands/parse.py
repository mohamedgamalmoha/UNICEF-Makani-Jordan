import os
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand


FRONTEND_DIR = getattr(settings, 'FRONTEND_DIR', settings.BASE_DIR / "templates")

HTML_ENCODING: str = 'utf-8'
HTML_BASE_FILENAME: str = getattr(settings, 'HTML_BASE_FILENAME', 'index.html')

STATIC_LOAD_TAG: str = '{% load static %}\n'
TAG_ATTR: dict = {
    'link': 'href',
    'script': 'src',
    'img': 'src',
}
STATIC_FILE_TYPES: dict = {
    'js': 'js',
    'css': 'css',
    'image': 'images'
}


def get_static_file_dir(filename: str):
    """Add file dir according to its type"""
    if filename.endswith('.js') and not filename.startswith('js'):
        return STATIC_FILE_TYPES.get('js') + '/' + filename
    elif filename.endswith('.css') and not filename.startswith('css'):
        return STATIC_FILE_TYPES.get('css') + '/' + filename
    elif not filename.startswith('images'):
        return STATIC_FILE_TYPES.get('image') + '/' + filename
    return filename


class Command(BaseCommand):
    """React Parser"""
    help = 'Parse base html file generated from react building process'

    def add_arguments(self, parser):
        parser.add_argument('--f', type=str)

    def handle(self, *args, **options):
        # reading html file
        filename = options.get('f') or HTML_BASE_FILENAME
        file_dir = os.path.join(FRONTEND_DIR, filename)
        with open(file_dir, 'r') as html_file:
            html = html_file.read()

        # parse html file and select link & script tags
        soup = BeautifulSoup(html, 'html.parser')
        print('Start parsing ...')
        for head in soup.select('link, script, img'):
            # get tag attribute (href or src)
            attr = TAG_ATTR.get(head.name, None)
            link = head.get(attr, None)
            # exclude CDNs
            if link is None or link.startswith('https://') or (link.startswith('{%') and link.endswith('%}')):
                continue
            print(head[attr], end=' --> ')
            # remove static word from link
            cleaned_link = link.replace(f'/static/', '')
            # check whether the dir is added at first, add it if not
            if not cleaned_link.endswith(tuple(STATIC_FILE_TYPES.keys())):
                cleaned_link = get_static_file_dir(cleaned_link)
            # modify link to match django template format
            new_attr = f"{{% static '{cleaned_link}' %}}"
            print(new_attr)
            head[attr] = new_attr
        print('Successfully parsed file "%s"' % filename)

        # writing back to html
        with open(os.path.join(FRONTEND_DIR, filename), "wb") as html_file_output:
            html_file_output.write(STATIC_LOAD_TAG.encode(HTML_ENCODING))
            html_file_output.write(soup.prettify(HTML_ENCODING))
        print('Successfully changed file "%s"' % filename)
