#!/usr/bin/env python3
from parlement_parser import ParliamentarySession
import os
import sys

OUTPUT_PATH = "build"

def print_usage():
    print(f'{sys.argv[0]} <base_url> <session> <session> ...')
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print_usage()
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    for session in sys.argv[2:]:
        session = int(session)
        parliamentary_session = ParliamentarySession(session)
        parliamentary_session.dump_json(OUTPUT_PATH, sys.argv[1])
if __name__ == "__main__":
    main()