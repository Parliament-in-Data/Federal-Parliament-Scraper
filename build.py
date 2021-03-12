#!/usr/bin/env python3
from parliament_parser import ParliamentarySession
import os
import sys
import json
from os import path, makedirs

OUTPUT_PATH = "build"

def print_usage():
    print(f'{sys.argv[0]} <base_url> <session> <session> ...')
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_usage()
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    sessions = {}
    for session in sys.argv[2:]:
        session = int(session)
        parliamentary_session = ParliamentarySession(session)
        sessions[session] = parliamentary_session.dump_json(OUTPUT_PATH, sys.argv[1])
    makedirs(OUTPUT_PATH, exist_ok=True)

    with open(path.join(OUTPUT_PATH, 'index.json'), 'w+') as fp:
        json.dump(sessions, fp, ensure_ascii='false')
if __name__ == "__main__":
    main()