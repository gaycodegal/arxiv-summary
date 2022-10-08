# arXiv Summarizer

Summarize some formats from arXiv.

This is not intended as a universal summarizer, but
I'm trying to summarize some fairly Regular-ly formatted
physics papers that seem to have been generated with LaTeX.

The pipeline is intended to be download PDF, run this
script, and then read with screen reader.

Attempts to extract Title, a couple of Authors,
Abstract, Introduction, and Conclusion.

Meant for linux.

To give context, 'some formats' means *only* scientific article
formats that have an abstract, introduction, and conclusion.

'Summarize' is not a magic term, this is not doing any
textual analysis, its purely trying to pull out the
abstract, introduction, and conclusion to the paper for you
so that you can know what the paper contains should you
ever want to give it a full read.

## Installation

```shell
pip3 install beautifulsoup4
```

I think pdftohtml comes from poppler-utils so

```shell
sudo apt install poppler-utils
```

## Usage

```
usage: basic-extractor.py [-h] [--out-folder OUT_FOLDER] [--clean | --no-clean]
                          [--debug-text | --no-debug-text]
                          [--temp-prefix TEMP_PREFIX]
                          pdf [pdf ...]

positional arguments:
  pdf                   the pdf of the paper to summarize like ./test.pdf

options:
  -h, --help            show this help message and exit
  --out-folder OUT_FOLDER
                        folder in which to store summarized texts (default: ./)
  --clean, --no-clean   whether to delete intermediary files (default: True)
  --debug-text, --no-debug-text
                        whether to write /tmp/output.txt debug file (default: False)
  --temp-prefix TEMP_PREFIX
                        destination of temporary files, prefix (default: /tmp/output)
```

## Text to speech

I'd recommend using https://github.com/foobnix/LibreraReader/releases
 which is downloadable from there or https://f-droid.org/.

I use it with the stock google voice `English (United States) > Voice V`
which I find pleasant for reading long texts. You could also
try RHVoice on android or on your computer, as well as Festvox/Festival
on your computer, which has multiple voices to choose from if
you install them, as well as the ability to convert text into
a wav file with text2wav (configured using your festival dot file).
Then convert the wav to mp3 to save on space if sending off to
a phone.

For any text to speech method you can always do:

```
cat *.txt > ../bundled_readings.txt
```

to combine individual text documents into one big document.
This means you can play multiple documents without pause /
in a row, if you really wanted to.

## Method

The papers I looked at pdftohtml was able to generate a
document outline from the pdf. I assume latex had some
hand in this as pdf readers could see the outline too.

As the outline details the headers of sections, we can grab
the introduction and conclusion/summary header from that list
using regex.

The outline is also useful because it has headers in order, so
we can just use the header of the introduction as a regex start
point and the header of the next section as the regex end point for
instance.

Abstract is usually not included in the pdf outline, so we search for
the abstract from wherever the word 'abstract' appears, to the first
header listed in the document outline.

Metadata is harder to extract, but it comes before the abstract, and
we hope in the same page as the abstract. If its on its own page
the script will break as it stands.

Metadata we assume is before the abstract, the first line that does not
include the words arXiv or latex we take to be the title.

The authors and universities are probably on lines including commas ','.
However, there are often a large number of authors and universities.
Because we are preparing the summary for text to speech (TTS),
we only want to get a few of these for the summary for context, but
not so many as it becomes long. Thus we search for lines containing
commas, and accept lines with commas in them up until we reach
4 commas. This filtering is only for the metadata section.
For each line containing commas that we accepted, we accept the first
two items in that list. So a,b,c becomes a,b.

## Papers tested on

- [A new approach to spectral approximation](https://arxiv.org/abs/1403.7120)
- [A Search for Wandering Black Holes in the Milky Way with Gaia and DECaLS](https://arxiv.org/abs/2105.04581)
    - For some reason this paper doesn't have an intro, so the summary doesn't include one.
- [Crawling the Cosmic Network: Exploring the Morphology of Structure in the Galaxy Distribution](https://arxiv.org/abs/0903.3601)
- [Inferences on relations between distant supermassive black holes and their hosts complemented by the galaxy fundamental plane](https://arxiv.org/abs/2204.11948)
- [Megamaser Disks Reveal a Broad Distribution of Black Hole Mass in Spiral Galaxies](https://arxiv.org/abs/1606.00018)
