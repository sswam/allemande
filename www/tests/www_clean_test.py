from www_clean import *


def test_html_title():
    ht = "foo <title>\n\nthe &amp; title\n</title> baz"
    expect = "the & title"
    assert html_title(ht) == expect

def test_html_title_none():
    ht = "foo bar"
    expect = ""
    assert html_title(ht) == expect


def test_html_main_content_main():
    ht = """foo\n<main id="x">\n\nhello </main> bar"""
    expect = "hello"
    assert html_main_content(ht) == expect

def test_html_main_content_article():
    ht = """foo\n<article id="x">\n\nhello </article> bar"""
    expect = "hello"
    assert html_main_content(ht) == expect

def test_html_main_content_role_main():
    ht = """foo\n<div id="foo" role="main">\n\n<div>hello</div> world </div> bar"""
    expect = "<div>hello</div> world"
    assert html_main_content(ht) == expect

def test_html_main_content_none():
    ht = """foo\n<div id="foo" role="bar">\n\n<div>hello</div> world </div> bar"""
    expect = ht
    assert html_main_content(ht) == expect

def test_html_main_content_wikipedia():
    for end in ["See_also", "References"]:
        ht = f"""foo <meta name="generator" content="MediaWiki">
foo
<div id="bodyContent">
hello
<h2><span class="mw-headline" id="{end}">{end}</h2>
bar"""
        expect = """<div id="bodyContent">\nhello\n"""
        assert html_main_content(ht) == expect
