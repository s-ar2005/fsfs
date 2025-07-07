#!/usr/bin/env python3
import sys
import os
from lib import Fsfs
def cmd_create(args):
    if len(args) != 2:
        print("Usage: fsfs create <fsfsfile> <dir>")
        return 1
    fsfsfile, dirpath = args
    if not os.path.isdir(dirpath):
        print(f"Error: {dirpath} is not a directory")
        return 1
    fsfs = Fsfs()
    print(f"Packing directory {dirpath} into {fsfsfile} ...")
    fsfs.pack_dir(dirpath)
    fsfs.save(fsfsfile)
    print("Done.")
    return 0

def cmd_write(args):
    if len(args) != 3:
        print("Usage: fsfs write <fsfsfile> <internal_dir_path> <local_file_path>")
        return 1
    fsfsfile, internal_dir_path, local_file = args
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    if not os.path.isfile(local_file):
        print(f"Error: {local_file} does not exist")
        return 1
    with open(local_file, 'rb') as f:
        data = f.read()
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    try:
        fsfs.add_file(internal_dir_path, os.path.basename(local_file), data)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    fsfs.save(fsfsfile)
    print(f"Written {local_file} into {internal_dir_path} in {fsfsfile}")
    return 0

def cmd_mount(args):
    if len(args) != 2:
        print("Usage: fsfs mount <fsfsfile> <mountdir>")
        return 1
    fsfsfile, mountdir = args
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    print(f"Extracting {fsfsfile} into {mountdir} ...")
    fsfs.extract(mountdir)
    print("Done.")
    return 0

def cmd_extract(args):
    if len(args) != 3:
        print("Usage: fsfs extract <fsfsfile> <internal_path> <outdir>")
        return 1
    fsfsfile, internal_path, outdir = args
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    print(f"Extracting '{internal_path}' from {fsfsfile} into {outdir} ...")
    try:
        fsfs.extract_path(internal_path, outdir)
    except FileNotFoundError:
        print(f"Error: path '{internal_path}' not found inside fsfs")
        return 1
    print("Done.")
    return 0

def cmd_ls(args):
    if len(args) != 1:
        print("Usage: fsfs ls <fsfsfile>")
        return 1
    fsfsfile = args[0]
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    fsfs.print_tree()
    return 0

def cmd_create_dir(args):
    if len(args) != 2:
        print("Usage: fsfs mkdir <fsfsfile> <internal_dir_path>")
        return 1
    fsfsfile, internal_dir_path = args
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    try:
        dirname = input("Enter new directory name: ").strip()
        if not dirname:
            print("Invalid directory name")
            return 1
        fsfs.create_dir(internal_dir_path, dirname)
        fsfs.save(fsfsfile)
        print(f"Directory '{dirname}' created in '{internal_dir_path}'")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except FileExistsError as e:
        print(f"Error: {e}")
        return 1
    return 0


def cmd_delete(args):
    if len(args) != 2:
        print("Usage: fsfs rm <fsfsfile> <internal_path>")
        return 1
    fsfsfile, internal_path = args
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    try:
        fsfs.delete(internal_path)
        fsfs.save(fsfsfile)
        print(f"Deleted '{internal_path}'")
    except (FileNotFoundError, IsADirectoryError) as e:
        print(f"Error: {e}")
        return 1
    return 0


def cmd_rename(args):
    if len(args) != 3:
        print("Usage: fsfs ren <fsfsfile> <internal_path> <new_name>")
        return 1
    fsfsfile, internal_path, new_name = args
    if not os.path.isfile(fsfsfile):
        print(f"Error: {fsfsfile} does not exist")
        return 1
    fsfs = Fsfs()
    fsfs.load(fsfsfile)
    try:
        fsfs.rename(internal_path, new_name)
        fsfs.save(fsfsfile)
        print(f"Renamed '{internal_path}' to '{new_name}'")
    except (FileNotFoundError, FileExistsError) as e:
        print(f"Error: {e}")
        return 1
    return 0

def main():
    if len(sys.argv) < 2:
        print("Usage: fsfs <command> [...args]")
        print("Commands: create, mount, ls, extract, write, mkdir, rm, ren")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "create":
        sys.exit(cmd_create(args))
    elif cmd == "mount":
        sys.exit(cmd_mount(args))
    elif cmd == "ls":
        sys.exit(cmd_ls(args))
    elif cmd == "extract":
        sys.exit(cmd_extract(args))
    elif cmd == "write":
        sys.exit(cmd_write(args))
    elif cmd == "mkdir":
        sys.exit(cmd_create_dir(args))
    elif cmd == "rm":
        sys.exit(cmd_delete(args))
    elif cmd == "ren":
        sys.exit(cmd_rename(args))
    else:
        print(f"Unknown command {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
