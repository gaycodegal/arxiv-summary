#!/usr/bin/python3
"""
Summarize some formats from arxiv.

This is not intended as a universal summarizer, but
I'm trying to summarize some fairly Regular-ly formatted
physics papers that seem to have been generated with LaTeX.

The pipeline is intended to be download PDF, run this
script, and then read with screen reader.

relies on pdftohtml being installed
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
                print("could not find '{}'".format(term))
                continue

            next_li = match.find_next("li")
            if next_li:
                next_li = next_li.find('a').get_text()
            sections[i] = [match.find('a').get_text(), next_li]
        return [('abstract', soup.find('li').get_text())] + sections
        

def convert_html_to_text(filename):
    with open(filename, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')

        # pdftohtml writes <filename> in the title elements
        # and sprinkles them throughout the file.
        # not useful so remove them
        titles= soup.find_all('title')
        for title in titles:
            title.extract()

        return soup.get_text()

dotted_number = re.compile('((?:\d+\.?)+)')
def number_dotter(match):
    return match.group(0) + "\.?"
def get_section_search_regex(section_title):
    # hack as some papers seem to have '1 title' in the TOC
    # but '1. title' in the paper
    # brittle AF
    section_title = re.escape(section_title)
    section_title = dotted_number.sub(number_dotter, section_title)
    return section_title.replace("\ ", "\s")
    
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
        print("'{}' not found".format(section_title))
        return ""
    end = len(text) - 1
    if next_section_title is not None:
        re_next_section_title = get_section_search_regex(next_section_title)
        end = re.search(re_next_section_title, text, re.M | re.I)
        if not end:
            print("'{}' not found".format(next_section_title))
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
    for filename in [output_tmp_name + "s.html", output_tmp_name + "-html.html", output_tmp_name + ".txt"]:
        if os.path.exists(filename):
            os.remove(filename)


def main(args):
    # first convert pdf into 2 html documents
    output_tmp_name = "/tmp/output"
    remove_intermediaries(output_tmp_name)
    subprocess.run(["pdftohtml", "-i", "-s", args.pdf, output_tmp_name], capture_output=True)
    
    # things we want to pull out
    # Title, Author, Universities, Abstract, Introduction, conclusion
    sections_to_find = ["intro", "conclu"]
    # gets: Abstract, Introduction, Conclusion
    sections = get_section_titles(output_tmp_name + "s.html", sections_to_find)
    text = convert_html_to_text(output_tmp_name + "-html.html")

    for i, section in enumerate(sections):
        if section is None:
            continue
        start, end = section
        print(find_section(text, start, end))

    # cleanup
    if args.clean:
        remove_intermediaries(output_tmp_name)
    if args.debug_text:
        with open(output_tmp_name + ".txt", "w") as tmp_out:
            tmp_out.write(text)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', help='the pdf of the paper to summarize like ./test.pdf')
    parser.add_argument('--clean', help='whether to keep intermediary files', default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument('--debug-text', help='whether to write /tmp/output.txt debug file', default=False, action=argparse.BooleanOptionalAction)
    #parser.add_argument('--html', help='temp arg; output-html.html')
    #parser.add_argument('--index', help='temp arg; outputs.html')
    args = parser.parse_args()
    main(args)
