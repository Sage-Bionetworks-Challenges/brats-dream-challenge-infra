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
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar_ref, path=path, members=members)
            imgs = [member.name for member in members]
    else:
        imgs = []

    return imgs
