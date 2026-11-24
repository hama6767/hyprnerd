#!/usr/bin/env python3
"""Create a reproducible release archive from the committed Git tree."""
import argparse, gzip, hashlib, pathlib, re, subprocess
R=pathlib.Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--output',type=pathlib.Path,default=R/'dist')
    args=parser.parse_args()
    if not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z._-]*',args.version):parser.error('Invalid version')
    prefix='hyprnerd-'+args.version
    args.output.mkdir(parents=True,exist_ok=True)
    destination=args.output/(prefix+'.tar.gz')
    # Git archive preserves executable bits and symlinks, and includes hidden files.
    data=subprocess.check_output(['git','-C',str(R),'archive','--format=tar','--prefix='+prefix+'/','HEAD'])
    destination.write_bytes(gzip.compress(data,compresslevel=9,mtime=0))
    checksum=hashlib.sha256(destination.read_bytes()).hexdigest()
    (args.output/'SHA256SUMS').write_text(checksum+'  '+destination.name+'\n')
    print(destination)
    print(checksum)
if __name__=='__main__':main()
