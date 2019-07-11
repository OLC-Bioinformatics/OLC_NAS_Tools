#!/usr/bin/env python

import os
import logging
import argparse
import requests
from nastools import retrieve_nas_files, parse_seqid_file
try:
    from accessoryFunctions.accessoryFunctions import SetupLogging
except ImportError:
    from olctools.accessoryFunctions.accessoryFunctions import SetupLogging

API_ENDPOINT = 'https://olc.cloud.inspection.gc.ca/metadata/olndata/'


def retrieve_oln_files(oln_ids, outdir, filetype, copyflag=False, split_oln=False, quality=['Reference'], verboseflag=False,
                       max_per_strain=10):
    """
    Uses the API provided by CFIA FoodPort to figure out which SeqIDs are associated with an OLN ID, and then
    grabs files.
    :param oln_ids: List of OLN IDs.
    :param outdir: Directory to store files in.
    :param filetype: Type of files to grab. Must be either fasta or fastq
    :param copyflag: If True, will copy files, if False, will create links.
    :param split_oln: If True, create a separate subfolder for each OLN ID in outdir. If false, all files are put into
    outdir
    :param quality: List with qualities to grab. Only acceptable entries in list are Fail, Pass, and Reference.
    :param verboseflag: If True, outputs will be more verbose.
    :param max_per_strain: Maximum number of sequence files to retrieve per strain.
    :return:
    """
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    for oln_id in oln_ids:
        seqids_to_get = list()
        response = requests.get(API_ENDPOINT + oln_id.upper(), verify=False)  # SSL Cert isn't good :(
        seqid_data = response.json()
        for seqid in seqid_data:
            if seqid_data[seqid] in quality:
                if len(seqids_to_get) < max_per_strain:
                    logging.info('Grabbing SeqID {} (quality {}) for OLN ID {}.'.format(seqid, seqid_data[seqid], oln_id))
                    seqids_to_get.append(seqid)
        if split_oln:
            oln_outdir = os.path.join(outdir, oln_id)
            if not os.path.isdir(oln_outdir):
                os.makedirs(oln_outdir)
        else:
            oln_outdir = outdir
        retrieve_nas_files(seqids=seqids_to_get,
                           outdir=oln_outdir,
                           copyflag=copyflag,
                           filetype=filetype,
                           verbose_flag=verboseflag)


def nastools_oln_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file',
                        required=True,
                        type=str,
                        help='File containing OLN IDs to extract, one ID per line.')
    parser.add_argument('-o', '--outdir',
                        required=True,
                        type=str,
                        help='Directory to copy/link files to. Will be created if it does not exist.')
    parser.add_argument("--type", "-t",
                        action='store',
                        required=True,
                        type=str,
                        choices=['fasta', 'fastq'],
                        help="Format of files to retrieve. Options are either fasta or fastq")
    parser.add_argument("--copy", "-c",
                        action='store_true',
                        help="Setting this flag will copy the files instead of creating relative symlinks")
    parser.add_argument("--verbose", "-v",
                        action='store_true',
                        help="Setting this flag will enable debugging messages")
    parser.add_argument('-s', '--split_on_oln',
                        default=False,
                        action='store_true',
                        help='Activate this flag to have a subfolder created in your outdir for each OLN ID. Files for '
                             'each OLN ID will be put into their respective subfolder.')
    parser.add_argument('-q', '--quality',
                        nargs='+',
                        choices=['Fail', 'Pass', 'Reference'],
                        default=['Reference'])
    parser.add_argument('-m', '--max_per_strain',
                        type=int,
                        default=10,
                        help='Maximum number of sequences to retrieve per strain. Defaults to 10.')
    args = parser.parse_args()

    SetupLogging(args.verbose)
    oln_ids = parse_seqid_file(args.file)
    retrieve_oln_files(oln_ids=oln_ids,
                       outdir=args.outdir,
                       filetype=args.type,
                       quality=args.quality,
                       verboseflag=args.verbose,
                       copyflag=args.copy,
                       split_oln=args.split_on_oln,
                       max_per_strain=args.max_per_strain)


if __name__ == '__main__':
    nastools_oln_cli()
