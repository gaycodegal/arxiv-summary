#!/usr/bin/python3
"""
Summarize some formats from arxiv.

This is not intended as a universal summarizer, but
I'm trying to summarize some fairly Regular-ly formatted
physics papers that seem to have been generated with LaTeX.

The pipeline is intended to be download PDF, run this
script, and then read with screen reader.

Attempts to extract Title, a couple of Authors,
Abstract, Introduction, and Conclusion.

*Relies on pdftohtml being installed.*
"""
from bs4 import BeautifulSoup
import re
import argparse
import subprocess
import os
import traceback

abstract_regex = re.compile('abstract|overview', re.I)
def get_section_titles_from_overview(html_filename, search_terms):
    """gets the section titles from s.html based on
both search terms, as well as the abstract.

search terms is a list of regexes to search for

returns a set of terms which define ranges to copy text
from. May return (a, b) (a, None) or None"""
    with open(html_filename, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')
        sections = [None] * len(search_terms)
        for i, term in enumerate(search_terms):
            match = soup.find('li', text=re.compile(term, re.I))
            if not match:
                print("could not find '{}'".format(term))
                continue

            next_li = match.find_next('li')
            if next_li:
                next_li = next_li.find('a').get_text()
            sections[i] = [match.find('a').get_text(), next_li]
        last_li = soup.find_all('li')
        if last_li is not None and len(last_li) > 1:
            last_li = last_li[-1].get_text()
        else:
            last_li = None

        next_after_abstract = soup.find('li')
        if next_after_abstract is not None:
            next_after_abstract = next_after_abstract.find('a').get_text()

        return [[abstract_regex, next_after_abstract]] + sections, last_li

def get_section_titles_from_paper(html_filename, search_terms, el_type = 'b'):
    """gets the section titles from -html.html based on
both search terms, as well as the abstract.

search terms is a list of regexes to search for

returns a set of terms which define ranges to copy text
from. May return (a, b) (a, None) or None"""
    with open(html_filename, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')
        sections = [None] * len(search_terms)
        for i, term in enumerate(search_terms):
            match = soup.find(el_type, text=re.compile(term, re.I))
            if not match:
                print("could not find '{}'".format(term))
                continue

            next_el = match.find_next(el_type)
            if next_el:
                next_el = next_el.get_text()
            sections[i] = [match.get_text(), next_el]
        last_el = soup.find_all(el_type)
        if last_el is not None and len(last_el) > 1:
            last_el = last_el[-1].get_text()
        else:
            last_el = None
        next_after_abstract = None
        # we're searching the paper itself for headers
        # this time, instead of the li document overview
        # and thus logic is more complicated
        abstract = soup.find(text=abstract_regex)
        if abstract is not None:
            abstract = abstract.find_parent(el_type)
            if abstract is not None:
                next_after_abstract = abstract.find_next(el_type)
            if next_after_abstract is not None:
                next_after_abstract = next_after_abstract.get_text()
        if next_after_abstract == None:
            next_after_abstract = soup.find_next(el_type)
            if next_after_abstract is not None:
                next_after_abstract = next_after_abstract.get_text()
        return [[abstract_regex, next_after_abstract]] + sections, last_el

re_title_raw = re.compile('^(?:\d+\.?)+\n(?:\w\ ?)+', re.M)
def get_section_titles_from_raw_text(text, headers_to_find):
    """gets the section titles from raw text of -html.html
based on both search terms, as well as the abstract.

search terms is a list of regexes to search for

returns a set of terms which define ranges to copy text
from. May return (a, b) (a, None) or None"""
    # hope that 1.1.1\nHeader is what the header format is
    headers = re_title_raw.findall(text)
    sections = [None] * len(headers_to_find)

    # compare all headers with all search terms
    for term_i, term in enumerate(headers_to_find):
        for header_i, header in enumerate(headers):
            if re.search(term, header, re.I | re.M):
                next_header = None
                if header_i + 1 < len(headers):
                    next_header = headers[header_i + 1]
                sections[term_i] = [header, next_header]
        if sections[term_i] is None:
            print("could not find '{}'".format(term))

    # abstract still probably wont have a number but at least
    # we know what its called well.
    last_header = None
    abstract_region = [abstract_regex, None]
    if len(headers) > 0:
        abstract_region[1] = headers[0]
        last_header = headers[-1]
    return [abstract_region] + sections, last_header
        

def convert_html_to_text(filename):
    """converts -html.html to text"""
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
    """replacer function 1 -> 1\.?"""
    return match.group(0) + "\.?"

def get_section_search_regex(section_title):
    """replaces spaces with \s to aid in newline avoidance
an puts an optional period after the first number just
in case"""
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
    start = None
    re_section_title = section_title
    if type(re_section_title) == str:
        re_section_title = get_section_search_regex(section_title)
        start = re.search(re_section_title, text, re.M | re.I)
    else:
        start = re_section_title.search(text)
    if not start:
        print("'{}' not found".format(section_title))
        return ""

    # include the title of the section
    start = start.start()

    end = 0
    # in case start >= end, keep trying to find a later instance
    # of the next_section_title
    if next_section_title is not None:
        re_next_section_title = next_section_title
        if type(re_next_section_title) == str:
            re_next_section_title = get_section_search_regex(next_section_title)
            re_next_section_title = re.compile(re_next_section_title, re.M | re.I)
        while (end is not None) and (end < start):
            end = re_next_section_title.search(text, pos = end + 1)
            if end is not None:
                end = end.start()
        if not end:
            print("'{}' not found (end '{}')".format(next_section_title, section_title))
            return ""
    else:
        end = len(text) - 1

    if start >= end:
        print(section_title, ">", next_section_title)
        return ""
    return text[start:end]

def remove_intermediaries(output_tmp_name):
    """delete various temporary files created
during pdf conversion"""
    for filename in [output_tmp_name + "s.html", output_tmp_name + "-html.html", output_tmp_name + ".txt"]:
        if os.path.exists(filename):
            os.remove(filename)

is_latex = re.compile("latex", re.I)
total_commas = 0
def is_desired_paragraph(p):
    """ignore any line with arXiv or latex in it.
if there's too many commas encountered thus far,
ignore"""
    global total_commas
    if "arXiv" in p:
        return False
    if is_latex.search(p):
        return False
    comma_count = p.count(",")
    if comma_count > 0:
        if total_commas > 4:
            return False
        else:
            total_commas += comma_count
    return True

def reduce_name_length(p):
    """If there are too many names on a line, shorten the line
to the first 2 names"""
    if p.count(",") > 0:
        return ",".join(p.split(",")[:2])
    return p

def extract_initial_metadata(output_tmp_name):
    """converts -html.html to text"""
    global total_commas
    total_commas = 0
    filename = output_tmp_name + "-html.html"
    with open(filename, "r") as html:
        soup = BeautifulSoup(html, 'html.parser')

        # get everything before abstract
        abstract = soup.find(text=re.compile("abstract", re.I))
        paragraphs = None
        if abstract is None:
            paragraphs = soup.find_all("p")[:3][::-1]
        else:
            abstract = abstract.find_parent("p")
            paragraphs = abstract.find_all_previous("p")
        # reverse the list because we were searching backwards
        paragraphs = [p.get_text() for p in paragraphs][::-1]
        paragraphs = filter(is_desired_paragraph, paragraphs)
        paragraphs = map(reduce_name_length, paragraphs)
        return "\n".join(paragraphs)


def extract_known_titled_sections(out, sections, text):
    """gets: Abstract, Introduction, Conclusion"""

    for i, section in enumerate(sections):
        if section is None:
            continue
        start, end = section
        out.write(find_section(text, start, end))
        out.write("\n\n")

# keeps track of titles so we don't overwrite a file
used_titles = {}
re_valid_filename = re.compile(r'[^\w\d-]')
def get_paper_txt_handle(args, title):
    """use the title as the name of the file,
but if multiple papers have the same title,
deduplicate them"""
    title_dedup_counter = 0
    if title in used_titles:
        title_dedup_counter += 1
        while title + str(title_dedup_counter) in used_titles:
            title_dedup_counter += 1
    if title_dedup_counter > 0:
        title = "{} ({})".format(title, title_dedup_counter)
    used_titles[title] = True
    return open(os.path.join(args.out_folder, title + '.txt'), 'w')

def extract_one_paper(paper_path, args, i):
    """extracts a single pdf to a text document or stdout"""
    # first convert pdf into 2 html documents
    output_tmp_name = args.temp_prefix
    remove_intermediaries(output_tmp_name)
    subprocess.run(["pdftohtml", "-i", "-s", paper_path, output_tmp_name], capture_output=True)
    # now we have created an index
    # outputs.html
    # and the actual page content
    # output-html.html

    # things we want to pull out
    # Title, Author, Universities, Abstract, Introduction, conclusion

    # Title, Author, Universities
    metadata = extract_initial_metadata(output_tmp_name)
    title = metadata.split("\n")[0]
    title = re_valid_filename.sub('_', title)
    print("processing '{new_title}' ({src_title}) ({n}/{total})".format(
        new_title=title[:30] + "...",
        src_title=os.path.split(paper_path)[-1][:10] + "...",
        n=i,
        total=len(args.pdf)))
    out = get_paper_txt_handle(args, title)
    out.write(metadata)
    out.write('\n')
    metadata = None

    text = convert_html_to_text(output_tmp_name + "-html.html")
    sections_to_find = ["intro", "conclu|summary|finding"]
    sections, last_section = get_section_titles_from_overview(
        output_tmp_name + "s.html", sections_to_find)
    # try to find section headers as bolded text
    if sections.count(None) == len(sections_to_find):
        print("searching for bolded titles")
        sections, last_section = get_section_titles_from_paper(output_tmp_name + "-html.html", sections_to_find, 'b')
    # try to find section headers as 1.2.3\ntitle
    if sections.count(None) == len(sections_to_find):
        print("attempting raw text title extraction")
        sections, last_section = get_section_titles_from_raw_text(text, sections_to_find)

    # attempt to remove references first (you wouldn't want to hear them in TTS)

    # last section index compared so that we don't remove text we're searching for
    last_section_index = -1
    if last_section is not None:
        last_section_index = text.rfind(last_section) + len(last_section)
    text_lower = text.lower()
    last_reference_index = max(text_lower.rfind("reference"), text_lower.rfind("bibliography"), last_section_index)
    text_lower = None
    if last_reference_index > 0:
        text = text[:last_reference_index]

    # Abstract, Introduction, conclusion
    extract_known_titled_sections(out, sections, text)

    # cleanup
    if args.clean:
        remove_intermediaries(output_tmp_name)
    if args.debug_text:
        with open(output_tmp_name + ".txt", "w") as tmp_out:
            tmp_out.write(text)

def main(args):
    for i, pdf in enumerate(args.pdf):
        try:
            extract_one_paper(pdf, args, i + 1)
        except:
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('pdf', help='the pdf of the paper to summarize like ./test.pdf', nargs='+')
    parser.add_argument('--out-folder', help='folder in which to store summarized texts', default="./")
    parser.add_argument('--clean', help='whether to delete intermediary files', default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument('--debug-text', help='whether to write /tmp/output.txt debug file', default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument('--temp-prefix', help='destination of temporary files, prefix', default='/tmp/output')
    args = parser.parse_args()
    main(args)
