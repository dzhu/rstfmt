#!/usr/bin/env python3

# As a hack, necessary since setuptools doesn't support SOURCE_DATE_EPOCH, set all mtimes in the
# given tar.gz files to a consistent value.

import gzip
import io
import os
import shutil
import sys
import tarfile


def edit_file(fn, epoch):
    buf = io.BytesIO()
    with open(fn, "rb") as in_file:
        shutil.copyfileobj(in_file, buf)
    buf.seek(0)

    with tarfile.open(mode="r", fileobj=buf) as in_tar, gzip.GzipFile(
        fn, "wb", mtime=epoch
    ) as gz, tarfile.open(mode="w", fileobj=gz) as out_tar:
        for m in in_tar.getmembers():
            m.mtime = epoch
            m.pax_headers["mtime"] = str(epoch)
            out_tar.addfile(m, in_tar.extractfile(m))


def main():
    epoch = int(os.environ["SOURCE_DATE_EPOCH"])
    for fn in sys.argv[1:]:
        edit_file(fn, epoch)


if __name__ == "__main__":
    main()
