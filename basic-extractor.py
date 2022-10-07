#!/usr/bin/python3
"""
Summarize some formats from arxiv.

This is not intended as a universal summarizer, but
I'm trying to summarize some fairly Regular-ly formatted
physics papers that seem to have been generated with LaTeX.

The pipeline is intended to be download PDF, run this
script, and then read with screen reader.
"""
from bs4 import BeautifulSoup
import re
import argparse
import subprocess
import os
# 1 run
#
# now we have created an index
# outputs.html
# and the actual page content
# output-html.html

def get_section_titles(html_filename, search_terms):
    with open(html_filename, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')
        sections = [None] * len(search_terms)
        for i, term in enumerate(search_terms):
            match = soup.find('li', text=re.compile(term, re.I))
            if not match:
                continue

            next_li = match.find_next("li")
            if next_li:
                next_li = next_li.get_text()
            sections[i] = (match.get_text(), next_li)

        return [('abstract', soup.find('li').get_text())] + sections
        

def convert_html_to_text(filename):
    with open(filename, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()

def get_section_search_regex(section_title):
    return re.escape(section_title).replace("\ ", "\s")
    
def find_section(text, section_title, next_section_title = None):
    """
we assume section_title and next_section_title will form the
start and end of a set of <p> paragraphs that will
be more or less the whole contents of that section.

We can do a regular search of the text if we
replace spaces with \s which will get around the
whole title segments being in different <p> tags

if next_section_title is None, will go until end of text
    """
    # convert "hi you" into "hi\syou" but safely
    re_section_title = get_section_search_regex(section_title)
    start = re.search(re_section_title, text, re.M | re.I)
    if not start:
        print(section_title, "not found")
        return ""
    end = len(text) - 1
    if next_section_title is not None:
        re_next_section_title = get_section_search_regex(next_section_title)
        end = re.search(re_next_section_title, text, re.M | re.I)
        if not end:
            print(next_section_title, "not found")
            return ""
        end = end.start()

    # include the title of the section
    start = start.start()
    if start >= end:
        print(section_title, ">", next_section_title)
        return ""
    return text[start:end]

def remove_intermediaries(output_tmp_name):
    # remove intermediary files
    for filename in [output_tmp_name + "s.html", output_tmp_name + "-html.html"]:
        if os.path.exists(filename):
            os.remove(filename)


def main(args):
    # first convert pdf into 2 html documents
    output_tmp_name = "/tmp/output"
    subprocess.run(["pdftohtml", "-i", "-s", args.pdf, output_tmp_name], capture_output=True)
    
    # things we want to pull out
    # Title, Author, Universities, Abstract, Introduction, conclusion
    sections_to_find = ["intro", "conclu"]
    # gets: Abstract, Introduction, Conclusion
    sections = get_section_titles(output_tmp_name + "s.html", sections_to_find)
    text = convert_html_to_text(output_tmp_name + "-html.html")

    for i, (start, end) in enumerate(sections):
        print(find_section(text, start, end))

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', help='the pdf of the paper to summarize like ./test.pdf')
    #parser.add_argument('--html', help='temp arg; output-html.html')
    #parser.add_argument('--index', help='temp arg; outputs.html')
    args = parser.parse_args()
    main(args)
