import markdown
from html.parser import HTMLParser

class _HTMLStrip(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return ''.join(self.parts)


def md_to_html(text):
    return markdown.markdown(text)

def html_to_txt(text):
    parser = _HTMLStrip()
    parser.feed(text)
    return parser.get_text()

def txt_to_upper(text):
    return text.upper()

CONVERTERS = {
    "md:html":   md_to_html,
    "html:text": html_to_txt,
    "txt:upper": txt_to_upper,
}
