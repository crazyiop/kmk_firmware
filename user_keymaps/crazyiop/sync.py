import shutil
from filehash import FileHash
from git import Repo
from pathlib import Path
from subprocess import run
from time import sleep

drives = [Path('/media/iop/') / side for side in ['IRISL', 'IRISR']]


repo = Repo('.', search_parent_directories=True)
source = Path(repo.working_tree_dir) / 'kmk'

hasher = FileHash('md5')


def scan(p, drive):
    res = False
    if p.is_dir():
        for f in p.iterdir():
            res |= scan(f, drive)
        return res

    if str(p).endswith('swp'):
        return False

    target = drive / Path(*p.parts[5:])
    res |= sync(p, target)
    return res


def sync(source, target):
    new_hash = hasher.hash_file(source)
    try:
        target_hash = hasher.hash_file(target)
    except FileNotFoundError:
        target_hash = 'no'
    if new_hash != target_hash:
        print(f'copy {source}  {new_hash}  ---->     {target} {target_hash}')
        shutil.copy(source, target)
        return True
    return False


sleep(0.1)
changed = False
for drive in drives:
    if drive.is_dir():

        changed |= scan(source, drive)
        changed |= sync(Path('code.py'), drive / 'code.py')
        changed |= sync(Path('hsvpixel.py'), drive / 'hsvpixel.py')
        if changed:
            # flush os buffer
            run(['sync'])
    else:
        print(f'drive {drive} not present')

