import markdown_it
from markdown_it import MarkdownIt

md_parser = MarkdownIt()
md_parser.disable("escape")

tokens = md_parser.parse(text)

def process_tokens(tokens):
    nonlocal has_math
    for token in tokens:
        if token.children:
            process_tokens(token.children)
        if token.type == 'link_open':
            token.attrs['href'] = fix_link(token.attrs['href'], bb_file)
        if token.type == 'image':
            pass
