# OLC NAS Tools

## Install
```
pip install olcnastools
```

## Help
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

