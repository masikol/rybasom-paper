#!/usr/bin/env python3

import os
import sys
import argparse

# == Parse arguments ==

parser = argparse.ArgumentParser()

# Input files

parser.add_argument(
    '-f',
    '--in-fasta-file',
    help='fasta file of SSU gene sequences',
    required=True
)

parser.add_argument(
    '-r',
    '--rfam',
    help='fasta file of SSU gene sequences',
    required=True
)

# Output files

parser.add_argument(
    '--outdir',
    help='output file for cmscan',
    required=True
)

# Dependencies

parser.add_argument(
    '--cmscan',
    help='cmscan executable',
    required=True
)


args = parser.parse_args()

# For convenience
fasta_seqs_fpath = os.path.abspath(args.in_fasta_file)
rfam_fpath = os.path.abspath(args.rfam)
outdpath = os.path.abspath(args.outdir)
cmscan_fpath = os.path.abspath(args.cmscan)


# Check existance of all input files and dependencies
for fpath in (fasta_seqs_fpath, rfam_fpath, cmscan_fpath):
    if not os.path.exists(fpath):
        print(f'Error: file `{fpath}` does not exist!')
        sys.exit(1)
    # end if
# enb for

# Check if seqkit executable is actually executable
if not os.access(cmscan_fpath, os.X_OK):
    print(f'Error: file `{cmscan_fpath}` is not executable!')
    sys.exit(1)
# end if

# Create output directory if needed
if not os.path.isdir(outdpath):
    try:
        os.makedirs(outdpath)
    except OSError as err:
        print(f'Error: cannot create directory `{outdpath}`')
        sys.exit(1)
    # end try
# end if

print(fasta_seqs_fpath)
print(rfam_fpath)
print(cmscan_fpath)
print()


# Heder for reformatted .tblout files
tblout_header = 'target_name\taccession\tquery_name\taccession\tmdl\tmdl_from\tmdl_to\tseq_from\tseq_to\tstrand\ttrunc\tpass\tgc\tbias\tscore\tEvalue\tinc\tdescription_of_target'


def reformat_tblout(tblout_fpath: str, tblout_header: str) -> None:
    # Function reformats .tblout file, which is output of cmscan.
    # Raw .tblout file is awfully formatted: fields are delimited by spaces
    #   (sometimes 2, sometimes 3 etc). And columns names caontain spaces too.
    # We will reformat tis file: rename columns according to `tblout_header`
    #   and replace irregular field delimiter with tabs.

    # Read all lines except of those starting with #
    with open(tblout_fpath, 'rt') as tblout_file:
        lines = list(
            map(
                str.strip,
                filter(
                    lambda x: x[0] != '#',
                    tblout_file.readlines()
                )
            )
        )
    # end with

    # Remove multiple spaces with single space
    for i in range(len(lines)):
        for space_num in range(20, 1, -1):
            lines[i] = lines[i].replace(' '*space_num, ' ')
        # end for
    # end for

    # Remove spaces in important fields with underscores
    for i in range(len(lines)):
        lines[i] = lines[i].replace('Bacterial small subunit ribosomal RNA', 'Bacterial_small_subunit_ribosomal_RNA')
        lines[i] = lines[i].replace('Archaeal small subunit ribosomal RNA', 'Archaeal_small_subunit_ribosomal_RNA')
    # end for

    # Replace spaces with tabs
    for i in range(len(lines)):
        lines[i] = lines[i].replace(' ', '\t')
    # end for

    # Write result lines to original file
    with open(tblout_fpath, 'wt') as tblout_file:
        tblout_file.write(f'{tblout_header}\n')
        tblout_file.write('\n'.join(lines) + '\n')
    # end with
# end def reformat_tblout


output_file = os.path.join(outdpath, 'cmscan_output.txt')
tblout_fpath = os.path.join(outdpath, 'cmscan_output_table.tblout')

command = ' '.join([
    cmscan_fpath,
    f'--tblout {tblout_fpath}',
    '--toponly --acc',
    rfam_fpath,
    fasta_seqs_fpath,
    f'> {output_file}',
    f'2> {output_file}'
])


print('Running cmscan command:')
print(command)
print('It will take a while: single sequence is processed for ~3 seconds')
print('To check progress, run this command (it will list all seqIDs of processed sequences):')
print(f'  grep -c "Query:" {output_file}')

exit_code = os.system(command)
if exit_code != 0:
    print('Error!')
# end if

print(f'Reformatting output file `{tblout_fpath}`...')
reformat_tblout(tblout_fpath, tblout_header)
print('Done')



# /home/cager/Misc_soft/infernal/infernal-1.1.4/bin/cmscan \
#   --tblout /mnt/1.5_drive_0/16S_scrubbling/archaea/cmscan_tblout/archaea_all_no_NNN_cmscan.tblout \
#   --toponly --cpu 4 --acc \
#   /mnt/1.5_drive_0/16S_scrubbling/rfam/RF01959.14.6.cm \
#   /mnt/1.5_drive_0/16S_scrubbling/archaea/gene_seqs/archaea_gene_seqs_no_NNN.fasta \
#   > /mnt/1.5_drive_0/16S_scrubbling/archaea/cmscan_tblout/archaea_all_no_NNN_cmscan.txt \
#   2> /mnt/1.5_drive_0/16S_scrubbling/archaea/cmscan_tblout/archaea_all_no_NNN_cmscan.txt

print('\nCompleted!')
print(output_file)
print(tblout_fpath)
