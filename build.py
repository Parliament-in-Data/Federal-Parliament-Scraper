#!/usr/bin/env python3
from scraper.parliament_session import ParliamentarySession
import sys
import json
from os import path, makedirs
from distutils.dir_util import copy_tree
from data_store import DataStore, JsonDataStore, CompoundDataStore

OUTPUT_PATH = 'build'
STATIC_SITE_PATH = 'static'


def session_to_URL(session):
    session = int(session)
    assert 52 <= session <= 55, 'Only sessions 52-55 are available via this API'
    session_info = ParliamentarySession.sessions[session]
    base_URI = sys.argv[1]
    output_path = 'build'
    base_path = path.join(output_path, 'sessions', str(session))
    base_URI = f'{base_URI}sessions/{session}/'
    data_store = CompoundDataStore([JsonDataStore(session, session_info['from'], session_info['to'], base_path, base_URI)])
    parliamentary_session = ParliamentarySession(session, data_store)
    parliamentary_session.store()
    return path.join(base_URI, 'session.json')


def print_usage():
    print(f'{sys.argv[0]} <base_url> <session> <session> ...')


def main():
    from multiprocessing import Pool, cpu_count
    if len(sys.argv) <= 1 or sys.argv[1] == '--help':
        print_usage()
    makedirs(OUTPUT_PATH, exist_ok=True)

    #with Pool(processes=min(cpu_count(), len(sys.argv[2:]))) as p:
    #    urls = p.map(session_to_URL, sys.argv[2:])

    urls = list(map(session_to_URL, sys.argv[2:])) # single-threaded version
    sessions = {value: urls[idx] for idx, value in enumerate(sys.argv[2:])}

    makedirs(OUTPUT_PATH, exist_ok=True)
    copy_tree('static', 'build')
    with open(path.join(OUTPUT_PATH, 'index.json'), 'w') as fp:
        json.dump(sessions, fp, ensure_ascii='false')


if __name__ == '__main__':
    main()
