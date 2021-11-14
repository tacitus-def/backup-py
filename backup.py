#!/bin/env python3

import os
import re
import sys
import uuid
import errno
import getopt
import subprocess
from glob import glob
from datetime import datetime


def backup_target(key, path_fs, path_conf, name, files, target_dir, exclude_file):
    now = datetime.now()
    dt = now.strftime("%Y-%m-%d-%H-%M-%S")
    snar_file = os.path.join(path_fs, "{0}_{1}.snar".format(name, key))
    incremental_flag = os.path.exists(snar_file)
    archive_file = os.path.join(path_fs, "{0}_{1}_{2}_{3}.tgz".format(name, key, dt, "incr" if incremental_flag else "full"))
    cmd_archive = ["/usr/bin/tar", "-c", "--one-file-system", "-z", "-f", archive_file, "-g", snar_file, "-C", target_dir]
    if exclude_file:
        if os.path.exists(exclude_file): 
            cmd_archive.append("-X")
            cmd_archive.append(exclude_file)
            with open(exclude_file, "r") as fh:
                print("Exclude file(s):", ", ".join(list(map(lambda a: a.strip(), fh.readlines()))))
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), exclude_file)
    cmd_archive += files
    print("Backup started at {0}".format(now.strftime("%d/%m/%Y, %H:%M:%S")))
    if incremental_flag:
        print("New incremental backup: {0}".format(archive_file))
    else:
        print("New full backup: {0}".format(archive_file))
    subprocess.call(cmd_archive)
    return archive_file


def process(path_base, name, target_dir, include_files, exclude_file = False, force = False):
    key = False
    path_fs = os.path.join(path_base, "fs")
    path_conf = os.path.join(path_base, "conf")
    if not force:
        files = sorted(glob(os.path.join(path_fs, name + "*_full.tgz")), reverse=True)
        if len(files) > 0:
            last_file = files.pop(0)
            last = os.path.basename(last_file)
            regexp = "^" + name + "_([a-f0-9]{32})_\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}_full\.tgz$"
            match = re.search(regexp, last)
            if match:
                key = match[1]
                print("Found full backup: {0}".format(last_file))
                print("Existing key: {0}".format(key))
    else:
        print("Forced full backup")
    if not key:
        key = uuid.uuid4().hex
        print("Generate new key: {0}".format(key))
    archive_file = backup_target(key, path_fs, path_conf, name, include_files, target_dir, exclude_file)
    print("Backup file size: {0}".format(os.path.getsize(archive_file)))
    return archive_file


def main():
    name = False 
    files = []
    force = False
    target = False
    path_base = "/backup"
    exclude_file = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'n:t:e:b:i:f', ['name=', 'target=', 'exclude=', 'base=', 'include=', 'force']) 
        for opt, arg in opts:
            if opt in ("-n", "--name"):
                name = arg
            elif opt in ("-b", "--base"):
                path_base = arg
            elif opt in ("-f", "--force"):
                force = True
            elif opt in ("-t", "--target"):
                target = arg
            elif opt in ("-e", "--exclude"):
                exclude_file = arg
            elif opt in ("-i", "--include"):
                files.append(arg)
        if len(files) == 0:
            files.append(".")
        if name and target:
            backup_file = process(path_base, name, target, files, exclude_file, force)
            now = datetime.now()
            print("Backup ended at {0}".format(now.strftime("%d/%m/%Y, %H:%M:%S")))
            print("------")
            sys.exit(0)
        else:
            print("Help: -n <name> -t <target>", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(3)
    except getopt.GetoptError as e:
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()

