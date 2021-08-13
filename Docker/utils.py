"""Common util functions for validation and scoring."""
import os
import tarfile
import zipfile


def _is_hidden(member):
    """Check whether file is hidden or not."""
    hidden = ("__", "._", "~", ".DS_Store")
    return os.path.split(member)[1].startswith(hidden)


def _filter_tar(members):
    """Filter out directory name and hidden files in tarball."""
    files_to_extract = []
    for member in members:
        if member.isfile() and not _is_hidden(member.name):
            files_to_extract.append(member)
    return files_to_extract


def _filter_zip(members):
    """Filter out directory name and hidden files in zip file."""
    files_to_extract = []
    for member in members:
        if not member.is_dir() and not _is_hidden(member.filename):
            files_to_extract.append(member.filename)
    return files_to_extract


def unzip_file(f, path="."):
    """Untar or unzip file."""
    if zipfile.is_zipfile(f):
        with zipfile.ZipFile(f) as zip_ref:
            imgs = _filter_zip(zip_ref.infolist())
            zip_ref.extractall(path=path, members=imgs)
    elif tarfile.is_tarfile(f):
        with tarfile.open(f) as tar_ref:
            members = _filter_tar(tar_ref)
            tar_ref.extractall(path=path, members=members)
            imgs = [member.name for member in members]
    else:
        imgs = []

    return imgs
