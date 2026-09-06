#!/usr/bin/env python3
"""Resume M57-Jean from its official S3 endpoint using validated byte ranges."""
import concurrent.futures
import os
from pathlib import Path
import re
import subprocess
import time

BASE = Path(__file__).resolve().parents[1]
EVIDENCE = BASE / 'evidence'
SOURCE = 'https://digitalcorpora.s3.amazonaws.com/corpora/drives/nps-2008-m57-jean'
SIZES = {'E01': 1572860321, 'E02': 1466890611}
CHUNK = 16 * 1024 * 1024

def fetch(task):
    ext, start, end, total, dest = task
    size = end - start + 1
    if dest.exists() and dest.stat().st_size == size:
        return size
    temporary = dest.with_suffix('.tmp')
    headers = dest.with_suffix('.headers')
    for attempt in range(4):
        result = subprocess.run([
            'curl', '--fail', '--silent', '--show-error', '--location',
            '--connect-timeout', '20', '--max-time', '180',
            '--speed-limit', '1024', '--speed-time', '30',
            '--range', f'{start}-{end}', '--dump-header', str(headers),
            '--output', str(temporary), f'{SOURCE}/nps-2008-jean.{ext}'
        ], capture_output=True, text=True)
        content_range = f'content-range: bytes {start}-{end}/{total}'
        if (result.returncode == 0 and temporary.exists()
                and temporary.stat().st_size == size
                and content_range in headers.read_text().lower()):
            temporary.replace(dest)
            return size
        print(f'Retry {attempt + 1}: {ext} bytes {start}-{end}: {result.stderr.strip()}', flush=True)
        time.sleep(2)
    raise RuntimeError(f'Download failed: {ext} bytes {start}-{end}; rerun to resume.')

def main():
    EVIDENCE.mkdir(exist_ok=True)
    lock = EVIDENCE / '.download.lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise SystemExit('Download lock exists. Ensure no other downloader is running before removing it.')
    try:
        tasks = []
        states = []
        for ext, total in SIZES.items():
            final = EVIDENCE / f'nps-2008-jean.{ext}'
            if final.exists():
                if final.stat().st_size != total:
                    raise RuntimeError(f'Unexpected size: {final}')
                continue
            partial = EVIDENCE / f'nps-2008-jean.{ext}.partial'
            partial.touch(exist_ok=True)
            start = partial.stat().st_size
            if start > total:
                raise RuntimeError(f'Oversized partial: {partial}')
            chunks = EVIDENCE / f'.{ext}-chunks'
            chunks.mkdir(exist_ok=True)
            segments = []
            for offset in range(start, total, CHUNK):
                end = min(offset + CHUNK, total) - 1
                dest = chunks / f'{offset}-{end}.chunk'
                tasks.append((ext, offset, end, total, dest))
                segments.append(dest)
            states.append((partial, final, total, segments))
        print(f'Downloading {len(tasks)} ranges with 12 connections; existing partial files preserved.', flush=True)
        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(fetch, task) for task in tasks]
            for future in concurrent.futures.as_completed(futures):
                completed += future.result()
                print(f'Validated ranges: {completed / 1024**2:.1f} MiB', flush=True)
        for partial, final, total, segments in states:
            with partial.open('ab') as stream:
                for segment in segments:
                    with segment.open('rb') as source:
                        while data := source.read(1024 * 1024):
                            stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if partial.stat().st_size != total:
                raise RuntimeError(f'Assembly size mismatch: {partial}')
            partial.replace(final)
            print(f'Complete: {final.name} ({total} bytes)', flush=True)
        subprocess.run(['bash', str(BASE / 'scripts/01_verify_evidence.sh'), str(EVIDENCE / 'nps-2008-jean.E01')], check=True)
        print('Checking EWF internal integrity...', flush=True)
        with (BASE / 'analysis/ewf_verification.txt').open('w') as out:
            subprocess.run(['ewfverify', str(EVIDENCE / 'nps-2008-jean.E01')], stdout=out, stderr=subprocess.STDOUT, check=True)
        print('EWF verification complete.', flush=True)
    finally:
        lock.rmdir()

if __name__ == '__main__':
    main()
