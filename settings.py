import os

"""New NAS"""
# TODO: this will eventually become /mnt/nas/, and old storage will be renamed to /mnt/nas2/
NAS_DIR = os.path.join('/mnt', 'nas2')

# fasta
PROCESSED_SEQUENCE_DATA_ROOT_DIR = os.path.join(NAS_DIR, 'processed_sequence_data')

# fastq
RAW_SEQUENCE_ROOT_DIR = os.path.join(NAS_DIR, 'raw_sequence_data')

"""Old NAS"""
NAS2_DIR = os.path.join('/mnt', 'nas')

# fasta
WGSSPADES = os.path.join(NAS2_DIR, 'WGSspades')
MERGE_WGSSPADES = os.path.join(NAS2_DIR, 'merge_WGSspades')
EXTERNAL_WGSSPADES = os.path.join(NAS2_DIR, 'External_WGSspades')
EXTERNAL_WGSSPADES_NONFOOD = os.path.join(NAS2_DIR, 'External_WGSspades', 'nonFood')

# fastq
MISEQ_BACKUP = os.path.join(NAS2_DIR, 'MiSeq_Backup')
MERGE_BACKUP = os.path.join(NAS2_DIR, 'merge_Backup')
EXTERNAL_MISEQ_BACKUP = os.path.join(NAS2_DIR, 'External_MiSeq_Backup')
