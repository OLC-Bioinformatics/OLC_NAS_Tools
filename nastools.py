import os
import glob
import errno
import shutil
import logging
import argparse
from collections import defaultdict
from settings import RAW_SEQUENCE_ROOT_DIR, PROCESSED_SEQUENCE_DATA_ROOT_DIR, MISEQ_BACKUP, MERGE_BACKUP, \
    EXTERNAL_MISEQ_BACKUP, WGSSPADES, MERGE_WGSSPADES, EXTERNAL_WGSSPADES, EXTERNAL_WGSSPADES_NONFOOD


def verify_folders():
    folders = [
        RAW_SEQUENCE_ROOT_DIR, PROCESSED_SEQUENCE_DATA_ROOT_DIR, MISEQ_BACKUP, MERGE_BACKUP,
        EXTERNAL_MISEQ_BACKUP, WGSSPADES, MERGE_WGSSPADES, EXTERNAL_WGSSPADES, EXTERNAL_WGSSPADES_NONFOOD
    ]
    for folder in folders:
        if not os.path.isdir(folder):
            logging.info('Could not find {}. Ensure the NAS is properly mounted.'.format(folder))
            quit()


def retrieve_nas_files(seqids, outdir, copyflag, filetype):
    """
    :param seqids: list containing valid OLC Seq IDs
    :param outdir: path to directory to dump requested files
    :param copyflag: boolean flag to determine with to copy files to create symlinks
    :param filetype: accepts string of either 'fastq' or 'fasta' to determine where to search for files
    """
    # Verify all target search folders are mounted
    verify_folders()

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
        for path in glob.iglob(os.path.join(RAW_SEQUENCE_ROOT_DIR, '*/*/*.fastq.gz')):
            file_dict[os.path.split(path)[1].split('_')[0]].append(path)
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
        for path in glob.iglob(os.path.join(PROCESSED_SEQUENCE_DATA_ROOT_DIR, '*/*/BestAssemblies/*.fasta')):
            file_dict[os.path.split(path)[1].split('.fasta')[0]].append(path)
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
                filepath = os.path.dirname(path)
                filename = os.path.basename(path)
                relpath = os.path.relpath(filepath, outdir)
                try:
                    if copyflag:
                        try:
                            shutil.copy(path, outdir)
                            logging.info('Copied {0} to {1}'.format(filename, os.path.join(outdir, filename)))
                        except shutil.SameFileError:
                            logging.info('A link to {} already exists in {}. Skipping...'.format(filename, outdir))
                    else:
                        os.symlink(os.path.join(relpath, filename),
                                   os.path.join(outdir, filename))
                        logging.info('Linked {0} to {1}'.format(filename, os.path.join(outdir, filename)))
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
    parser.add_argument("--copy", "-c", required=False, action='store_true', default=False,
                        help="Setting this flag will copy the files instead of creating symlinks")
    parser.add_argument("--type", "-t", action='store', required=True, type=str, choices=['fasta', 'fastq'],
                        help="Type of files to retrieve, i.e. fasta or fastq")
    parser.add_argument("--verbose", "-v", required=False, action='store_true', default=False,
                        help="Setting this flag will enable more verbose output")
    args = parser.parse_args()

    # Grab args
    seqids = args.file
    outdir = args.outdir
    copyflag = args.copy
    filetype = args.type
    verbose = args.verbose

    # Logging setup
    if not verbose:
        logging.basicConfig(format='\033[92m \033[1m %(asctime)s \033[0m %(message)s ',
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(format='\033[92m \033[1m %(asctime)s \033[0m %(message)s ',
                            level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')

    # Parse SeqIDs file
    seqids = parse_seqid_file(seqids)

    # Run script
    retrieve_nas_files(seqids, outdir, copyflag, filetype)

    logging.info('{} complete'.format(os.path.basename(__file__)))


if __name__ == '__main__':
    nastools_cli()
