#!/usr/bin/env python3
from parliament_parser import ParliamentarySession
import os
import sys
import json
from os import path, makedirs
from distutils.dir_util import copy_tree

OUTPUT_PATH = "build"
STATIC_SITE_PATH = "static"


def session_to_URL(session):
    session = int(session)
    parliamentary_session = ParliamentarySession(session)
    return parliamentary_session.dump_json(OUTPUT_PATH, sys.argv[1])


def print_usage():
    print(f'{sys.argv[0]} <base_url> <session> <session> ...')


def main():
    from multiprocessing import Pool, cpu_count
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_usage()
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    #with Pool(processes=min(cpu_count(), len(sys.argv[2:]))) as p:
    #    urls = p.map(session_to_URL, sys.argv[2:])

    urls = list(map(session_to_URL, sys.argv[2:])) # single-threaded version
    sessions = {value: urls[idx] for idx, value in enumerate(sys.argv[2:])}

    makedirs(OUTPUT_PATH, exist_ok=True)
    copy_tree("static", "build")
    with open(path.join(OUTPUT_PATH, 'index.json'), 'w+') as fp:
        json.dump(sessions, fp, ensure_ascii='false')


if __name__ == "__main__":
    main()
