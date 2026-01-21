#!/usr/bin/env python

"""
Script to retrieve FASTQ or FASTA files from the primary OLC NAS based on a
list of SEQ IDs.

Can either copy the files or create relative symbolic links to them.

Requires access to the OLC NAS at /mnt/nas2.

Usage:
    python nastools.py --file seqids.txt --outdir /path/to/output
    --type fastq [--copy] [--verbose]
"""

# Standard library imports
from glob import iglob
from importlib import metadata
import argparse
import logging
import os
import re
import shutil

__version__ = metadata.version('olcnastools')


class Retrieve:
    """
    Class to retrieve FASTQ or FASTA files from the primary OLC NAS based on a
    list of SEQ IDs.
    """

    def main(self):
        """
        Main function to run the retrieval process
        """
        self.verify_folders()
        self.locate_files()
        self.file_triage()
        self.missing_seqids()

    def verify_folders(self):
        """
        Ensure that the NAS is mounted, and contains all the expected folders
        """
        for folder in self.folders:
            if not os.path.isdir(folder):
                logging.error(
                    'Could not find %s. Ensure the NAS is properly mounted.',
                    folder
                )
                raise SystemExit(1)

    def locate_files(self):
        """
        Use iglob and supplied search patterns to search the new NAS. Populates
        dictionaries with seqid: list of paths
        """
        # Debug level logging
        logging.debug('Seq IDs provided: %s', ', '.join(sorted(self.seqids)))
        logging.debug('Output directory: %s', self.outdir)
        logging.debug('Copy flag: %s', self.copyflag)
        logging.debug('File format: %s', self.filetype)

        logging.info('Retrieving requested files')

        # Search the NAS!
        self.search_nas(
            nas=self.nas_folders,
            file_dict=self.new_file_dict
        )

    def search_nas(
        self,
        nas: list,
        file_dict: dict
    ):
        """
        Search for the supplied SEQ ID in the desired NAS (location)
        :param nas: the NAS to search (new vs only)
        :param file_dict: dictionary to populate for desired NAS
        """
        for directory, nested_dict in nas.items():
            try:
                # Extract the nested directory structure string
                for glob_string in nested_dict[self.filetype]:
                    # Use iglob to search for all files matching the supplied
                    # pattern
                    for path in iglob(
                        os.path.join(
                            directory,
                            glob_string,
                            self.extensions[self.filetype]
                        )
                    ):
                        # Extract the SEQ ID from the file path
                        sequence_id = os.path.basename(
                            list(
                                filer(
                                    filelist=[path],
                                    extension=self.filetype
                                )
                            )[0]
                        )
                        # Add the SEQ ID the file path to the dictionary
                        try:
                            file_dict[sequence_id].append(path)
                        except KeyError:
                            file_dict[sequence_id] = []
                            file_dict[sequence_id].append(path)
            except KeyError:
                pass

    def file_triage(self):
        """
        Process SEQ IDs depending on if they are found on the new NAS
        """
        for seqid in sorted(self.seqids):
            logging.critical(seqid)
            # Check to see if sequence files with the current SEQ ID were
            # found on the new NAS
            if seqid in self.new_file_dict:
                self.file_paths(
                    seqid=seqid,
                    file_dict=self.new_file_dict
                )
            else:
                self.missing.append(seqid)

    def file_paths(
        self,
        seqid: str,
        file_dict: dict
    ):
        """
        Process SEQ IDs depending on the number of sequence files found
        :param seqid: Current SEQ ID being processed
        :param file_dict: dictionary to populate for desired NAS
        """
        # Extract the list of paths from the dictionary
        paths = file_dict[seqid]
        if len(paths) > self.lengths:
            logging.error(
                'Located multiple copies of %s at the following locations: %s',
                seqid, ', '.join(set(os.path.dirname(path) for path in paths))
                )
            logging.error(
                'Please ensure that only a single copy is present on the NAS'
            )

        # Process the files
        self.process_files(path=sorted(paths)[0])
        # Add the paired reads for FASTQ files if they exist
        if self.filetype == 'fastq' and len(paths) > 1:
            self.process_files(path=sorted(paths)[1])

    def process_files(self, path):
        """
        Link/copy files as required
        :param path: Name and path of file to copy/link
        """
        # Extract the file name from the path string
        filename = os.path.basename(path)

        # Set the name and path of the file to output
        output_file = os.path.join(self.outdir, filename)
        logging.info('%s %s to %s', self.verb, path, output_file)

        # Don't try to add the file if it is already present in the folder
        if not os.path.isfile(output_file):
            if self.copyflag:
                shutil.copyfile(path, output_file)
            else:
                relative_symlink(
                    src_file=path,
                    output_dir=self.outdir
                )
        else:
            logging.warning(
                '%s already exists in %s. Skipping.',
                filename, self.outdir
            )

    def missing_seqids(self):
        """
        List all the SEQ IDs for which files could not be found
        """
        if self.missing:
            logging.error(
                'Files for the following SEQ IDs could not be located: %s',
                ', '.join(self.missing)
            )

    def __init__(self, seqids, outdir, copyflag, filetype, verboseflag):
        """
        :param seqids: list of SEQ IDs provided
        :param outdir: Directory in which sequence files are to be
        copied/linked
        :param copyflag: Boolean for whether files are to be copied of
        relatively symbolically linked
        :param filetype: File type to process: either FASTQ or FASTA
        :param verboseflag: Boolean for whether debug messages should be
        printed
        """
        # Configure the logging
        setup_logging(verboseflag)

        # Class variables from arguments
        self.seqids = seqids
        self.outdir = outdir

        # Make output directory if it doesn't exist.
        os.makedirs(self.outdir, exist_ok=True)

        # Class variables from arguments
        self.copyflag = copyflag
        self.filetype = filetype

        # Global setup of expected NAS folder structure
        # Set all the paths for the folders to use
        self.nas_dir = os.path.join('/mnt', 'nas2')
        self.processed_sequence_data = os.path.join(
            self.nas_dir, 'processed_sequence_data'
        )
        self.raw_sequence_data = os.path.join(
            self.nas_dir, 'raw_sequence_data'
        )

        # Dictionaries storing the path, the file type present in the folded
        # and the nested folder structure
        self.nas_folders = {
            self.raw_sequence_data: {'fastq': ['*/*']},
            self.processed_sequence_data: {'fasta': ['*/*/BestAssemblies']}
        }

        # List of all the folders
        self.folders = [folder for folder in self.nas_folders]
        # Glob patterns for each file type
        self.extensions = {
            'fastq': '*.fastq.gz',
            'fasta': '*.fasta'
        }

        # As FASTQ files are (usually) paired, only print a warning about
        # finding duplicate copies if more than two files are found; print
        # the warning if more than one FASTA file is found
        self.lengths = 2 if self.filetype == 'fastq' else 1

        # Set the term to use depending on whether files are copied or linked
        self.verb = 'Copying' if copyflag else 'Linking'

        # Dictionary to store sequence files on the related NAS
        self.new_file_dict = {}

        # A list to store SEQ IDs for which sequence files cannot be located
        self.missing = []


def parse_seqid_file(seqfile: str) -> list:
    """
    Read in a file of SEQ IDs, and return the list of IDs
    :param seqfile: Files containing a column of SEQ IDs
    :return: list of SEQ IDs to process
    """
    # Initialise list to hold SEQ IDs
    seqids = []
    with open(seqfile, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip()
            # Ignore empty lines
            if line:
                seqids.append(line)
    return seqids


def setup_logging(verbose_flag):
    """
    Setup logging configuration
    :param verbose_flag: BOOL flag to determine logging level
    """
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG if verbose_flag else logging.INFO
    )


def filer(
    filelist: list,
    extension: str = 'fastq',
    returndict: bool = False
) -> set or dict:
    """
    Helper script that creates a set of the stain names created by stripping
    off parts of the filename.
    Hopefully handles different naming conventions
    (e.g. 2015-SEQ-001_S1_L001_R1_001.fastq(.gz), 2015-SEQ-001_R1_001.fastq.gz,
    2015-SEQ-001_R1.fastq.gz, 2015-SEQ-001_1.fastq.gz, and
    2015-SEQ-001_1.fastq.gz all become 2015-SEQ-001)
    :param filelist: List of files to parse
    :param extension: the file extension to use. Default value is 'fastq
    :param returndict: type BOOL: Option to return a dictionary of file name:
    fastq files associated with that name
    rather than a set of the file names
    :return: either a set of file names or a dictionary of file name: fastq
    """
    # Initialise the variables
    fileset = set()
    filedict = {}

    # Build an extension regex that accepts optional .gz
    ext_re = fr"(?:\.{re.escape(extension)}(?:\.gz)?)$"

    # Stripping patterns ordered from most specific to least specific
    strip_patterns = [
        re.compile(
            r"_S\d+_L\d+(_R\d(_\d+)?)?", re.IGNORECASE
        ),  # _S24_L001_R1_001
        re.compile(
            r"_R\d_\d{3}", re.IGNORECASE
        ),  # _R1_001
        re.compile(
            r"_R\d_001", re.IGNORECASE
        ),  # _R1_001 (explicit)
        re.compile(
            r"_R\d", re.IGNORECASE
        ),  # _R1 / _R2
        re.compile(
            r"[-_]\d{1,3}(_\d{3})?$", re.IGNORECASE
        ),  # _001 or -1 etc
        re.compile(
            ext_re, re.IGNORECASE
        ),  # .fastq(.gz) or .fasta
    ]

    for seqfile in filelist:
        filename_only = os.path.basename(seqfile)
        file_name = filename_only
        for pat in strip_patterns:
            m = pat.search(file_name)
            if m:
                file_name = file_name[:m.start()]
                break

        file_name = file_name.rstrip('_-')  # final cleanup

        fileset.add(file_name)
        filedict.setdefault(file_name, []).append(seqfile)

    if returndict:
        return filedict
    return fileset


def relative_symlink(
    src_file: str,
    output_dir: str,
    output_name: str = None,
    export_output: bool = False
) -> str:
    """
    Create relative symlinks files - use the relative path from the desired
    output directory to the storage path
    e.g. ../../2013-SEQ-0072/simulated/40/50_150/simulated_trimmed
    2013-SEQ-0072_simulated_40_50_150_R1.fastq.gz
    is the relative path to the output_dir. The link name is the base name of
    the source file joined to the desired output directory
    e.g. output_dir/2013-SEQ-0072/2013-SEQ-0072_simulated_40_50_150_R1.fastq.gz
    https://stackoverflow.com/questions/9793631/creating-a-relative-symlink-in-python-without-using-os-chdir
    :param src_file: Source file to be symbolically linked
    :param output_dir: Destination folder for the link
    :param output_name: Optionally allow for the link to have a different name
    :param export_output: type BOOL: Optionally return the absolute path of
    the new, linked file
    :return output_file: type STR: Absolute path of the newly-created symlink
    """
    # Determine the file name for the symlink
    if output_name:
        file_name = output_name
    else:
        file_name = os.path.basename(src_file)

    # Set the output file path
    output_file = os.path.join(output_dir, file_name)

    # Create the relative symlink
    try:
        os.symlink(
            os.path.relpath(
                src_file,
                output_dir),
            output_file
        )
    # Ignore FileExistsErrors
    except FileExistsError:
        pass

    # Return the absolute path of the symlink if requested
    if export_output:
        return output_file


def retrieve_nas_files(
    seqids: list,
    outdir: str,
    filetype: str,
    copyflag: bool = False,
    verbose_flag: bool = False
):
    """
    :param seqids: LIST containing strings of valid OLC Seq IDs
    :param outdir: STRING path to directory to dump requested files
    :param filetype: STRING of either 'fastq' or 'fasta' to determine where to
    search for files
    :param copyflag: BOOL flag to determine if files should be copied or
    symlinked. Default False.
    :param verbose_flag: BOOL flag to determine logging level. Default False.
    """
    # Create the retrieve object
    retrieve = Retrieve(
        seqids=seqids,
        outdir=outdir,
        copyflag=copyflag,
        filetype=filetype,
        verboseflag=verbose_flag
    )

    # Run script
    retrieve.main()


def nastools_cli():
    """
    Command-line interface for the nastools package.
    """
    # Parser setup
    parser = argparse.ArgumentParser(
        description='Locate and copy/link either FASTQ or FASTA files on '
        'the primary OLC NAS.'
    )
    parser.add_argument(
        "--version",
        action='version',
        version=f'%(prog)s {__version__}',
        help="Print the version number and exit"
    )
    parser.add_argument(
        "--file", "-f",
        required=True,
        type=str,
        help="File containing list of SEQ IDs to extract"
    )
    parser.add_argument(
        "--outdir", "-o",
        required=True,
        type=str,
        help="Directory in which sequence files are to be copied/linked"
    )
    parser.add_argument(
        "--type", "-t",
        action='store',
        required=True,
        type=str,
        choices=['fasta', 'fastq'],
        help="Format of files to retrieve. Options are either fasta or fastq"
    )
    parser.add_argument(
        "--copy", "-c",
        action='store_true',
        help="Setting this flag will copy the files instead of creating "
        "relative symlinks"
    )
    parser.add_argument(
        "--verbose", "-v",
        action='store_true',
        help="Setting this flag will enable debugging messages"
    )
    args = parser.parse_args()

    # Grab args
    seqids = args.file
    outdir = args.outdir
    copyflag = args.copy
    filetype = args.type
    verboseflag = args.verbose

    # Parse SeqIDs file
    seqids = parse_seqid_file(seqids)

    # Create the retrieve object
    retrieve = Retrieve(
        seqids=seqids,
        outdir=outdir,
        copyflag=copyflag,
        filetype=filetype,
        verboseflag=verboseflag
    )

    # Retun the retrieve object
    return retrieve


def main():
    """
    Command-line entry point for the nastools package.

    This function builds the parser, parses arguments, constructs the
    retrieval object and runs the retrieval. It is suitable to be used
    as a console entry point (console_scripts or project.scripts).
    """
    nastools = nastools_cli()
    nastools.main()
    logging.info('%s complete', os.path.basename(__file__))


if __name__ == '__main__':
    main()
