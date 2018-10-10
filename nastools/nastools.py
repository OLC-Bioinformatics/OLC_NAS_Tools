#!/usr/bin/env python
from accessoryFunctions.accessoryFunctions import filer, make_path, relative_symlink, SetupLogging
from glob import iglob
import argparse
import logging
import shutil
import os


class Retrieve(object):

    def main(self):
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
                logging.error('Could not find {folder}. Ensure the NAS is properly mounted.'
                              .format(folder=folder))
                quit()

    def locate_files(self):
        """
        Use iglob and supplied search patterns to search the new NAS (and old one, too if necessary). Populates
        dictionaries with seqid: list of paths
        """
        # Debug level logging
        logging.debug('Seq IDs provided: {seq_list}'.format(seq_list=', '.join(sorted(self.seqids))))
        logging.debug('Output directory: {outdir}'.format(outdir=self.outdir))
        logging.debug('Copy flag: {copy}'.format(copy=self.copyflag))
        logging.debug('File format: {format}'.format(format=self.filetype))

        logging.info('Retrieving requested files')
        # Only look in the old NAS if one or more of the SEQ IDs could not be found in the primary NAS
        old_nas = False
        # Look in the new NAS first
        self.search_nas(nas=self.nas_folders,
                        file_dict=self.new_file_dict)
        # Check to see if sequence files for the current SEQ ID were found on the primary NAS
        for sequence_id in self.seqids:
            # If the file isn't on the new NAS, check the old NAS
            if sequence_id not in self.new_file_dict:
                old_nas = True
        if old_nas:
            self.search_nas(nas=self.old_nas_folders,
                            file_dict=self.old_file_dict)

    def search_nas(self, nas, file_dict):
        """
        Search for the supplied SEQ ID in the desired NAS (location)
        :param nas: the NAS to search (new vs old)
        :param file_dict: dictionary to populate for desired NAS
        """
        for directory, nested_dict in nas.items():
            try:
                # Extract the nested directory structure string
                for glob_string in nested_dict[self.filetype]:
                    # Use iglob to search for all files matching the supplied pattern
                    for path in iglob(os.path.join(directory,
                                                   glob_string,
                                                   self.extensions[self.filetype])):
                        # Extract the SEQ ID from the file path
                        sequence_id = os.path.basename(list(filer(filelist=[path],
                                                                  extension=self.filetype))[0])
                        # Add the SEQ ID the file path to the dictionary
                        try:
                            file_dict[sequence_id].append(path)
                        except KeyError:
                            file_dict[sequence_id] = list()
                            file_dict[sequence_id].append(path)
            except KeyError:
                pass

    def file_triage(self):
        """
        Process SEQ IDs depending on whether they are found on the new or old NAS
        """
        for seqid in sorted(self.seqids):
            logging.critical(seqid)
            # Check to see if sequence files with the current SEQ ID were found on the new NAS
            if seqid in self.new_file_dict:
                self.file_paths(seqid=seqid,
                                file_dict=self.new_file_dict)
            # Otherwise try the old NAS
            else:
                if seqid in self.old_file_dict:
                    self.file_paths(seqid=seqid,
                                    file_dict=self.old_file_dict)
                else:
                    self.missing.append(seqid)

    def file_paths(self, seqid, file_dict):
        """
        Process SEQ IDs depending on the number of sequence files found
        :param seqid: Current SEQ ID being processed
        :param file_dict: dictionary to populate for desired NAS
        """
        # Extract the list of paths from the dictionary
        paths = file_dict[seqid]
        if len(paths) > self.lengths:
            logging.error('Located multiple copies of {seqid} at the following locations: {loc}.'
                          .format(seqid=seqid,
                                  loc=', '.join(set(os.path.dirname(path) for path in paths))))
            logging.error('Please ensure that only a single copy is present on the NAS')
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
        logging.info('{verb} {path} to {out_file}'.format(verb=self.verb,
                                                          path=path,
                                                          out_file=output_file))
        # Don't try to add the file if it is already present in the folder
        if not os.path.isfile(output_file):
            if self.copyflag:
                shutil.copyfile(path, output_file)
            else:
                relative_symlink(src_file=path,
                                 output_dir=self.outdir)
        else:
            logging.warning('{seqid} already exists in {outdir}. Skipping.'
                            .format(seqid=filename,
                                    outdir=self.outdir))

    def missing_seqids(self):
        """
        List all the SEQ IDs for which files could not be found
        """
        if self.missing:
            logging.error('Files for the following SEQ IDs could not be located: {seqids}'
                          .format(seqids=', '.join(self.missing)))

    def __init__(self, seqids, outdir, copyflag, filetype, verboseflag):
        """
        :param seqids: list of SEQ IDs provided
        :param outdir: Directory in which sequence files are to be copied/linked
        :param copyflag: Boolean for whether files are to be copied of relatively symbolically linked
        :param filetype: File type to process: either FASTQ or FASTA
        :param verboseflag: Boolean for whether debug messages should be printed
        """
        # Configure the logging
        SetupLogging(verboseflag)
        # Class variables from arguments
        self.seqids = seqids
        self.outdir = outdir
        # Make output directory if it doesn't exist.
        make_path(self.outdir)
        self.copyflag = copyflag
        self.filetype = filetype
        # Global setup of expected NAS folder structure
        # TODO: this will eventually become /mnt/nas/, and old storage will be renamed to /mnt/nas2/
        # Set all the paths for the folders to use
        self.nas_dir = os.path.join('/mnt', 'nas2')
        self.processed_sequence_data = os.path.join(self.nas_dir, 'processed_sequence_data')
        self.raw_sequence_data = os.path.join(self.nas_dir, 'raw_sequence_data')
        self.merge_backup = os.path.join(self.nas_dir, 'raw_sequence_data', 'merged_sequences')
        # Old NAS
        self.old_nas = os.path.join('/mnt', 'nas')
        self.wgs_spades = os.path.join(self.old_nas, 'WGSspades')
        self.merge_wgs_spades = os.path.join(self.old_nas, 'merge_WGSspades')
        self.external_wgs_spades = os.path.join(self.old_nas, 'External_WGSspades')
        self.external_wgs_spades_nonfood = os.path.join(self.old_nas, 'External_WGSspades', 'nonFood')
        self.miseq_backup = os.path.join(self.old_nas, 'MiSeq_Backup')
        self.external_miseq_backup = os.path.join(self.old_nas, 'External_MiSeq_Backup')
        # Dictionaries storing the path, the file type present in the folder, and the nested folder structure
        self.nas_folders = {
            self.raw_sequence_data: {'fastq': ['*/*']},
            self.merge_backup: {'fastq': ['']},
            self.processed_sequence_data: {'fasta': ['*/*/BestAssemblies']}
        }
        self.old_nas_folders = {
            self.miseq_backup: {'fastq': ['*']},
            self.external_miseq_backup: {'fastq': ['*/*',
                                                   '*/*/*']},
            self.wgs_spades: {'fasta': ['*/BestAssemblies']},
            self.merge_wgs_spades: {'fasta': ['*/BestAssemblies']},
            self.external_wgs_spades: {'fasta': ['*/*/BestAssemblies']},
            self.external_wgs_spades_nonfood: {'fasta': ['*/*/BestAssemblies']}
        }
        # List of all the folders
        self.folders = [folder for folder in self.nas_folders] + [folder for folder in self.old_nas_folders]
        # Glob patterns for each file type
        self.extensions = {
            'fastq': '*.fastq.gz',
            'fasta': '*.fasta'
        }
        # As FASTQ files are (usually) paired, only print a warning about finding duplicate copies if more than
        # two files are found; print the warning if more than one FASTA file is found
        self.lengths = 2 if self.filetype == 'fastq' else 1
        # Set the term to use depending on whether files are copied or linked
        self.verb = 'Copying' if copyflag else 'Linking'
        # Dictionary to store sequence files on the related NAS
        self.new_file_dict = dict()
        self.old_file_dict = dict()
        # A list to store SEQ IDs for which sequence files cannot be located
        self.missing = list()


def parse_seqid_file(seqfile):
    """
    Read in a file of SEQ IDs, and return the list of IDs
    :param seqfile: Files containing a column of SEQ IDs
    :return: list of SEQ IDs to process
    """
    seqids = list()
    with open(seqfile) as f:
        for line in f:
            line = line.rstrip()
            seqids.append(line)
    return seqids


def nastools_cli():
    # Parser setup
    parser = argparse.ArgumentParser(description='Locate and copy/link either FASTQ or FASTA files on '
                                                 'the primary OLC NAS (the old NAS is searched if files cannot be '
                                                 'located on the primary.')
    parser.add_argument("--file", "-f",
                        required=True,
                        type=str,
                        help="File containing list of SEQ IDs to extract")
    parser.add_argument("--outdir", "-o",
                        required=True,
                        type=str,
                        help="Directory in which sequence files are to be copied/linked")
    parser.add_argument("--type", "-t",
                        action='store',
                        required=True,
                        type=str,
                        choices=['fasta', 'fastq'],
                        help="Format of files to retrieve. Options are either fasta or fastq")
    parser.add_argument("--copy", "-c",
                        required=False,
                        action='store_true',
                        default=False,
                        help="Setting this flag will copy the files instead of creating relative symlinks")
    parser.add_argument("--verbose", "-v",
                        required=False,
                        action='store_true',
                        default=False,
                        help="Setting this flag will enable debugging messages")
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
    retrieve = Retrieve(seqids=seqids,
                        outdir=outdir,
                        copyflag=copyflag,
                        filetype=filetype,
                        verboseflag=verboseflag)
    # Run script
    retrieve.main()
    logging.info('{} complete'.format(os.path.basename(__file__)))


if __name__ == '__main__':
    nastools_cli()
