#!/usr/bin/env python
# -*- coding: utf-8 -*-
''' Parallel NCBI download script '''
import sys, os, argparse
from subprocess import Popen, PIPE
from pipes import quote

from isolates import __version__, ceil
from source import acctypes
from isolates.metadata import (ExtractExperimentIDs_acc,
                               ExtractExperimentIDs_tax,
                               ExtractTaxIDfromSearchTerm)

def parse_args(args):
    ''' Parse command line parameters '''
    parser = argparse.ArgumentParser(
        description=('Download samples from NCBI through either a taxonomy or '
                     'accession ID input'))
    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='NCBI Downloader {ver}'.format(ver=__version__))
    parser.add_argument(
        '-a',
        metavar=('ACCESSION'),
        help=('Input should be a path to file containing accession IDs or a '
              'comma-separated string of accession IDs.\n'
              'The file may only contain one accession ID per line.\n')
    )
    parser.add_argument(
        '-t',
        metavar=('TAXID'),
        help=('Input should be a path to file containing taxonomy IDs or a '
              'comma-separated string of taxonomy IDs.\n'
              'The file may only contain one taxonomy ID per line.\n')
    )
    parser.add_argument(
        '-m',
        default=None,
        help=('JSON file with seed attributes (default fields and values) and '
              'mandatory fields.\n')
    )
    parser.add_argument(
        '-p',
        '--preserve',
        action="store_true",
        dest="preserve",
        default=False,
        help='Preserve any existing fastq files.\n'
    )
    parser.add_argument(
        '--all_runs_as_samples',
        action="store_true",
        dest="all_runs_as_samples",
        default=False,
        help=('Treat all runs associated to a sample as separate samples. '
              'Default is to combine them into one run.\n')
    )
    parser.add_argument(
        '-n',
        '--nodes',
        dest="nodes",
        default=1,
        help='Number of parallel batch jobs requested [default: 1]\n'
    )
    parser.add_argument(
        '-out',
        metavar=('OUTPUT'),
        required=True,
        help='output directory name.'
    )
    return parser.parse_args(args)

def SetupParallelDownload(accession_list):
    ''' Expand list of accession IDs to experiment or lower, and devide into
    parallel batch jobs
    '''
    experiments = []
    failed_accession = []
    with open(accession_list, 'r') as f:
        for l in f:
            accession = l.strip()
            if accession == '': continue
            # Determine accession type
            if accession[:3] in acctypes:
                accession_type = acctypes[accession[:3]]
            elif accession.isdigit(): # asume all integers to be taxids
                accession_type = "taxid"
            else:
                # Try searching for a matching Taxid from the search query
                taxid = ExtractTaxIDfromSearchTerm(accession)
                if taxid is not None:
                    print(("The query %s was identified to have the following "
                           "taxid: %s")%(accession, taxid))
                    accession_type = "taxid"
                    accession = taxid
                else:
                    print("unknown accession type for '%s'!"%accession)
                    failed_accession.append(accession)
                    continue
            print("Acc Found: %s (%s)"%(accession, accession_type))
            if accession_type in ['study', 'sample']:
                experiments.extend(ExtractExperimentIDs_acc(accession))
            elif accession_type in ['experiment', 'run']:
                experiments.append(accession)
            elif accession_type in ['taxid']:
                experiments.extend(ExtractExperimentIDs_tax(accession))
    if failed_accession:
        print("The following accessions were not downloaded!")
        print('\n'.join(failed_accession))
    else:
        print("All accessions downloaded succesfully!")
    return experiments

def GetCMD(prog, args):
    cmd = [prog]
    cmd.extend([str(x) if not isinstance(x, (unicode)) else x.encode('utf-8')
                for x in [quote(x) for x in args]])
    return ' '.join(cmd)

def main():
    args = parse_args(sys.argv[1:])
    if args.a is not None and args.t is not None:
        sys.exit('Usage: -a PATH/ACC -t PATH/TAX -out PATH [-m JSON]')
    experiments = []
    if args.a is not None:
        # Extract accession related experiments
        if os.path.exists(args.a):
            accfile = args.a
        elif args.a[:3] in acctypes:
            accfile = 'tmp.acc'
            with open(accfile, 'w') as f: f.write('\n'.join(args.a.split(',')))
        experiments.extend(SetupParallelDownload(accfile))
    if args.t is not None:
        # Extract tax id related experiments
        if os.path.exists(args.t):
            taxfile = args.a
        else:
            taxfile = 'tmp.tax'
            with open(taxfile, 'w') as f: f.write('\n'.join(args.t.split(',')))
        experiments.extend(SetupParallelDownload(taxfile))
    # Remove doublicate experiments
    experiments = list(set(experiments))
    elen = len(experiments)
    print("Found %s unique experiment Accessions IDs!"%(elen))
    if elen > 0:
        # Create out directory
        cwd = os.getcwd()
        out_dir = "%s/%s/"%(cwd, args.out)
        if not os.path.exists(out_dir): os.mkdir(out_dir)
        os.chdir(out_dir)
        # Split experiments in batches
        epb = ceil(elen / float(args.nodes))
        batches = [experiments[s:s+epb] for s in xrange(0,elen,epb)]
        # Run batch downloads
        ps = []
        for batch_dir, eids in enumerate(batches):
            # Save experiment IDs to file
            batch_acc_list = "%s/%s.acc"%(out_dir, batch_dir)
            with open(batch_acc_list, 'w') as f: f.write('\n'.join(eids))
            # Prepare cmdline
            nargs =['-a', batch_acc_list,
                    '-out', str(batch_dir)
                    ]
            if args.preserve: nargs.append('-p')
            if args.m is not None: nargs.extend(['-m', "%s/%s"%(cwd,args.m)])
            if args.all_runs_as_samples: nargs.append('--all_runs_as_samples')
            cmd = GetCMD("download-accession-list", nargs)
            # Execute batch download
            ps.append(Popen(cmd, shell=True, executable="/bin/bash"))
        # Wait for all batches to finish
        esum = 0
        for p in ps:
            esum += p.wait()
        if esum == 0:
            print('All batches finished succesfully!')
        else:
            print('Something failed!')
    else:
        print('No experiments could be found!')

if __name__ == "__main__":
    main()
