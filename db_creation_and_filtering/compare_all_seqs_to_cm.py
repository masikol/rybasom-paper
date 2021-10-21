#!/usr/bin/env python3

# The script compares gene sequences to specific Rfam covariance model to detect truncated genes.

# Input files:
# 1. -f/--in-fasta-file -- input fasta file of SSU gene sequences

# Output file:
# 1. -o/--outdir -- output directory for output files:
#   1) file `cmscan_output_table.tblout` -- TSV file of comparison statistics
#   2) file `cmscan_output.txt` -- txt file, contains complete output of cmscan.

# Dependencies:
# 1. --cmscan -- cmscan executable
# 2. --cmpress -- cmpress executable
# 3. -r/--rfam-family-cm -- Rfam covariane model (.cm) file to compare sequences to

print(f'\n|=== STARTING SCRIPT `{__file__}` ===|\n')


import os
import re
import sys
import argparse
import subprocess as sp


# == Parse arguments ==

parser = argparse.ArgumentParser()

# Input files

parser.add_argument(
    '-f',
    '--in-fasta-file',
    help='input fasta file of SSU gene sequences',
    required=True
)

# Output files

parser.add_argument(
    '--outdir',
    help='output directory',
    required=True
)

# Dependencies

parser.add_argument(
    '--cmscan',
    help='cmscan executable',
    required=True
)

parser.add_argument(
    '--cmpress',
    help='cmpress executable',
    required=True
)

parser.add_argument(
    '-r',
    '--rfam-family-cm',
    help=""".cm file containing covariance model of target gene family
  (RF00177 for bacterial ribosomal SSU, RF01959 for archaeal ribosomal SSU)""",
    required=True
)


args = parser.parse_args()

# For convenience
fasta_seqs_fpath = os.path.abspath(args.in_fasta_file)
rfam_fpath = os.path.abspath(args.rfam_family_cm)
outdpath = os.path.abspath(args.outdir)
cmscan_fpath = os.path.abspath(args.cmscan)
cmpress_fpath = os.path.abspath(args.cmpress)


# Check existance of all input files and dependencies
for fpath in (fasta_seqs_fpath, rfam_fpath, cmscan_fpath, cmpress_fpath):
    if not os.path.exists(fpath):
        print(f'Error: file `{fpath}` does not exist!')
        sys.exit(1)
    # end if
# enb for

# Check if executables are actually executable
for exec_fpath in (cmscan_fpath, cmpress_fpath):
    if not os.access(exec_fpath, os.X_OK):
        print(f'Error: file `{exec_fpath}` is not executable!')
        sys.exit(1)
    # end if
# end for

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
print(cmscan_fpath)
print(cmpress_fpath)
print(rfam_fpath)
print()


# Header for reformatted .tblout files
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


def run_cmpress(cmpress_fpath: str, rfam_fpath: str) -> None:
    # Function runs cmpress on rfam .cm file.
    # It is required to run cmscan.

    # Actually run cmpress
    print('Running `cmpress`...')
    cmd = f'{cmpress_fpath} {rfam_fpath}'
    pipe = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    stdout_stderr = pipe.communicate()

    if pipe.returncode != 0:
        # It something goes wrong -- check the error message
        error_msg = stdout_stderr[1].decode('utf-8')

        # If `error_msg` contains `already_exists_msg_pattern` -- it's ok --
        #   index files exist.
        already_exists_msg_pattern = r'.+ file ({}.+) already exists'.format(rfam_fpath)
        already_exists_obj = re.search(already_exists_msg_pattern, error_msg)
        just_already_exists = not already_exists_obj is None

        if just_already_exists:
            print(error_msg)
            print(f'Removing {already_exists_obj.group(1)}')
            os.unlink(already_exists_obj.group(1))
            run_cmpress(cmpress_fpath, rfam_fpath)
        else:
            # If `error_msg` does not contain `already_exists_msg_pattern` -- oh, we must terminate
            print('Error: cannot cmpress .cm file')
            print(error_msg)
            sys.exit(1)
        # end if
    else:
        # Print piped stdout
        print(stdout_stderr[0].decode('utf-8'))
    # end if
# end def run_cmpress


# == Proceed ==

# Index file with covariance model
run_cmpress(cmpress_fpath, rfam_fpath)


# Configure paths to output files
output_file = os.path.join(outdpath, 'cmscan_output.txt')
tblout_fpath = os.path.join(outdpath, 'cmscan_output_table.tblout')

# Configure command for cmscan
command = ' '.join([
    cmscan_fpath,
    f'--tblout {tblout_fpath}',
    '--toponly --acc',
    rfam_fpath,
    fasta_seqs_fpath,
    f'> {output_file}',
    f'2> {output_file}'
])


# == Proceed ==


print('Running cmscan command:')
print(command)
print('It will take a while: single sequence is processed for ~3 seconds')
print('To check progress, run this command (it will list all seqIDs of processed sequences):')
print(f'  grep -c "Query:" {output_file}')

exit_code = os.system(command)
if exit_code != 0:
    print('Error!')
# end if


# Reformat output .tblout table
print(f'Reformatting output file `{tblout_fpath}`...')
reformat_tblout(tblout_fpath, tblout_header)
print('Done')


print('\nCompleted!')
print(output_file)
print(tblout_fpath)
print(f'\n|=== EXITTING SCRIPT `{__file__}` ===|\n')
