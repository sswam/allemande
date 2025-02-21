from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTextInlineProcessor

class NoBrExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.deregister('linebreak')
#        md.inlinePatterns.deregister('hardbreak')
