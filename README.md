# OLC NAS Tools
[![PyPI version](https://badge.fury.io/py/olcnastools.svg)](https://badge.fury.io/py/olcnastools)

## Install
```
pip install olcnastools
```

## Usage
This program can either be used from the command line or imported directly in Python

#### Command Line:
```
usage: nastools.py [-h] --file FILE --outdir OUTDIR --type {fasta,fastq}
                   [--copy] [--verbose]

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE  File containing list of SEQ IDs to extract
  --outdir OUTDIR, -o OUTDIR
                        Out directory to link files to
  --type {fasta,fastq}, -t {fasta,fastq}
                        Type of files to retrieve, i.e. fasta or fastq
  --copy, -c            Setting this flag will copy the files instead of
                        creating symlinks
  --verbose, -v         Setting this flag will enable more verbose output

```

#### Accessing module in Python
```from nastools import retrieve_nas_files```

```
def retrieve_nas_files(seqids, outdir, filetype, copyflag=False, verbose_flag=False):
    """
    :param seqids: LIST containing strings of valid OLC Seq IDs
    :param outdir: STRING path to directory to dump requested files
    :param filetype: STRING of either 'fastq' or 'fasta' to determine where to search for files
    :param copyflag: BOOL flag to determine if files should be copied or symlinked. Default False.
    :param verbose_flag: BOOL flag to determine logging level. Default False.
    """
```
