#!/usr/bin/python3
from bs4 import BeautifulSoup
import re

# 1 run
#"pdftohtml -i -s %s output"
# now we have created an index
# outputs.html
# and the actual page content
# output-html.html


def convert_html_to_text(file_name):
    with open(file_name, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

def find_section(text, section_title, next_section_title):
    """
we assume section_title and next_section_title will form the
start and end of a set of <p> paragraphs that will
be more or less the whole contents of that section.

We can do a regular search of the text if we
replace spaces with \s which will get around the
whole title segments being in different <p> tags
    """
    # convert "hi you" into "hi\syou" but safely
    re_section_title, re_next_section_title = [re.escape(x).replace("\ ", "\s") for x in [section_title, next_section_title]]
    start = re.search(re_section_title, text, re.M | re.I)
    end = re.search(re_next_section_title, text, re.M | re.I)
    if not start:
        print(section_title, "not found")
        return ""
    if not end:
        print(next_section_title, "not found")
        return ""
    # include the title of the section
    start = start.start()
    end = end.start()
    if start >= end:
        print(section_title, ">", next_section_title)
        return ""
    return text[start:end]
    
def main():
    sections = ["abstract", "1. Introduction", "2. Galerkin spectral projections"]
    text = convert_html_to_text("output-html.html")
    for i in range(len(sections) - 1):
        print(find_section(text, sections[i], sections[i + 1]))
    
if __name__ == "__main__":
    main()
