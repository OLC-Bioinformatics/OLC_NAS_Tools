#!/usr/bin/env python

import os
import glob
import errno
import shutil
import logging
import argparse
from collections import defaultdict

# Global setup of expected NAS folder structure
# TODO: this will eventually become /mnt/nas/, and old storage will be renamed to /mnt/nas2/
NAS_DIR = os.path.join('/mnt', 'nas2')
PROCESSED_SEQUENCE_DATA_ROOT_DIR = os.path.join(NAS_DIR, 'processed_sequence_data')
RAW_SEQUENCE_ROOT_DIR = os.path.join(NAS_DIR, 'raw_sequence_data')

NAS2_DIR = os.path.join('/mnt', 'nas')
WGSSPADES = os.path.join(NAS2_DIR, 'WGSspades')
MERGE_WGSSPADES = os.path.join(NAS2_DIR, 'merge_WGSspades')
EXTERNAL_WGSSPADES = os.path.join(NAS2_DIR, 'External_WGSspades')
EXTERNAL_WGSSPADES_NONFOOD = os.path.join(NAS2_DIR, 'External_WGSspades', 'nonFood')
MISEQ_BACKUP = os.path.join(NAS2_DIR, 'MiSeq_Backup')
MERGE_BACKUP = os.path.join(NAS2_DIR, 'merge_Backup')
EXTERNAL_MISEQ_BACKUP = os.path.join(NAS2_DIR, 'External_MiSeq_Backup')


def setup_logging(verbose_flag):
    if not verbose_flag:
        logging.basicConfig(format='\033[92m \033[1m %(asctime)s \033[0m %(message)s ',
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(format='\033[92m \033[1m %(asctime)s \033[0m %(message)s ',
                            level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')


def verify_folders():
    folders = [
        RAW_SEQUENCE_ROOT_DIR, PROCESSED_SEQUENCE_DATA_ROOT_DIR, MISEQ_BACKUP, MERGE_BACKUP,
        EXTERNAL_MISEQ_BACKUP, WGSSPADES, MERGE_WGSSPADES, EXTERNAL_WGSSPADES, EXTERNAL_WGSSPADES_NONFOOD
    ]
    for folder in folders:
        if not os.path.isdir(folder):
            logging.info('Could not find {}. Ensure the NAS is properly mounted.'.format(folder))
            quit()


def retrieve_nas_files(seqids, outdir, copyflag, filetype, verbose_flag=False):
    """
    :param seqids: LIST containing strings of valid OLC Seq IDs
    :param outdir: STRING path to directory to dump requested files
    :param copyflag: BOOL flag to determine with to copy files to create symlinks
    :param filetype: STRING of either 'fastq' or 'fasta' to determine where to search for files
    :param verbose_flag: BOOL flag to determine logging level
    """
    # Logging
    setup_logging(verbose_flag)

    # Verify all target search folders are mounted
    verify_folders()

    # Make output directory if it doesn't exist.
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
        logging.info('Created new folder at {}'.format(outdir))

    logging.info('Retrieving requested files...')

    # Verbose logging
    logging.debug('Seq IDs provided:')
    for seqid in seqids:
        logging.debug(seqid)
    logging.debug('Output directory: {}'.format(outdir))
    logging.debug('Copy flag: {}'.format(copyflag))
    logging.debug('File type: {}'.format(filetype))

    # Preparing dictionary of all files
    file_dict = defaultdict(list)
    if filetype == 'fastq':
        logging.info('Searching all raw sequence data folders...')
        # New NAS
        for path in glob.iglob(os.path.join(RAW_SEQUENCE_ROOT_DIR, '*/*/*.fastq.gz')):
            file_dict[os.path.split(path)[1].split('_')[0]].append(path)

        # Old NAS
        for path in glob.iglob(os.path.join(MISEQ_BACKUP, '*/*.fastq.gz')):
            file_dict[os.path.split(path)[1].split('_')[0]].append(path)
        for path in glob.iglob(os.path.join(EXTERNAL_MISEQ_BACKUP, '*/*/*.fastq.gz')):
            file_dict[os.path.split(path)[1].split('_')[0]].append(path)
        for path in glob.iglob(os.path.join(MERGE_BACKUP, '*.fastq.gz')):
            file_dict[os.path.split(path)[1].split('_')[0]].append(path)
        for path in glob.iglob(os.path.join(EXTERNAL_MISEQ_BACKUP, '*/*/*/*.fastq.gz')):
            file_dict[os.path.split(path)[1].split('_')[0]].append(path)
    elif filetype == 'fasta':
        logging.info('Searching all processed sequence data folders...')
        # New NAS
        for path in glob.iglob(os.path.join(PROCESSED_SEQUENCE_DATA_ROOT_DIR, '*/*/BestAssemblies/*.fasta')):
            file_dict[os.path.split(path)[1].split('.fasta')[0]].append(path)

        # Old NAS
        for path in glob.iglob(os.path.join(WGSSPADES, '*/BestAssemblies/*.fasta')):
            file_dict[os.path.split(path)[1].split('.fasta')[0]].append(path)
        for path in glob.iglob(os.path.join(MERGE_WGSSPADES, '*/BestAssemblies/*.fasta')):
            file_dict[os.path.split(path)[1].split('.fasta')[0]].append(path)
        for path in glob.iglob(os.path.join(EXTERNAL_WGSSPADES, '*/*/BestAssemblies/*.fasta')):
            file_dict[os.path.split(path)[1].split('.fasta')[0]].append(path)
        for path in glob.iglob(os.path.join(EXTERNAL_WGSSPADES_NONFOOD, '*/*/BestAssemblies/*.fasta')):
            file_dict[os.path.split(path)[1].split('.fasta')[0]].append(path)

    # Iterate over requested SeqIDs
    missing_files = []
    for seqid in seqids:
        if seqid in file_dict:
            values = file_dict[seqid]
            for path in values:
                filename = os.path.basename(path)
                try:
                    if copyflag:
                        try:
                            shutil.copy(path, outdir)
                            logging.info('Copied {} to {}'.format(filename, os.path.join(outdir, filename)))
                        except shutil.SameFileError:
                            logging.info('A link to {} already exists in {}. Skipping...'.format(filename, outdir))
                    else:
                        os.symlink(path, os.path.join(outdir, filename))
                        logging.info('Linked {} to {}'.format(filename, os.path.join(outdir, filename)))
                except OSError as exception:
                    if exception.errno != errno.EEXIST:
                        raise
        else:
            missing_files.append(seqid)

    # Display any missing files
    if len(missing_files) > 0:
        logging.info('Missing Files:')
        for f in missing_files:
            logging.info(f)


def parse_seqid_file(seqfile):
    seqids = []
    with open(seqfile) as f:
        for line in f:
            line = line.rstrip()
            seqids.append(line)
    return seqids


def nastools_cli():
    # Parser setup
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", required=True, type=str,
                        help="File containing list of SEQ IDs to extract")
    parser.add_argument("--outdir", "-o", required=True, type=str,
                        help="Out directory to link files to")
    parser.add_argument("--type", "-t", action='store', required=True, type=str, choices=['fasta', 'fastq'],
                        help="Type of files to retrieve, i.e. fasta or fastq")
    parser.add_argument("--copy", "-c", required=False, action='store_true', default=False,
                        help="Setting this flag will copy the files instead of creating symlinks")
    parser.add_argument("--verbose", "-v", required=False, action='store_true', default=False,
                        help="Setting this flag will enable more verbose output")
    args = parser.parse_args()

    # Grab args
    seqids = args.file
    outdir = args.outdir
    copyflag = args.copy
    filetype = args.type
    verbose_flag = args.verbose

    # Parse SeqIDs file
    seqids = parse_seqid_file(seqids)

    # Run script
    retrieve_nas_files(seqids, outdir, copyflag, filetype, verbose_flag)

    logging.info('{} complete'.format(os.path.basename(__file__)))


if __name__ == '__main__':
    nastools_cli()
