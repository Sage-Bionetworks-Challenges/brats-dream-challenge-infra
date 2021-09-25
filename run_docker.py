"""Run training synthetic docker models"""
from __future__ import print_function
import argparse
import getpass
import os
import tarfile
import time
import glob
import json

import docker
import synapseclient


def create_log_file(log_filename, log_text=None, mode="w"):
    """Create log file"""
    print(log_text)
    with open(log_filename, mode) as log_file:
        if log_text is not None:
            if isinstance(log_text, bytes):
                log_text = log_text.decode("utf-8")
            log_file.write(log_text.encode("ascii", "ignore").decode("ascii"))
        else:
            log_file.write("No Logs")


def store_log_file(syn, log_filename, parentid, store=True):
    """Store log file"""
    statinfo = os.stat(log_filename)
    print(f"storing logs: {statinfo.st_size}")
    if statinfo.st_size > 0 and statinfo.st_size/1000.0 <= 50:
        ent = synapseclient.File(log_filename, parent=parentid)
        if store:
            try:
                syn.store(ent)
            except synapseclient.core.exceptions.SynapseHTTPError as err:
                print(err)


def remove_docker_container(container_name):
    """Remove docker container"""
    client = docker.from_env()
    try:
        cont = client.containers.get(container_name)
        cont.stop()
        cont.remove()
    except Exception:
        print("Unable to remove container")


def pull_docker_image(image_name):
    """Pull docker image"""
    client = docker.from_env()
    try:
        client.images.pull(image_name)
    except docker.errors.APIError:
        print("Unable to pull image")


def remove_docker_image(image_name):
    """Remove docker image"""
    client = docker.from_env()
    try:
        client.images.remove(image_name, force=True)
    except Exception:
        print("Unable to remove image")


def tar(directory, tar_filename):
    """Tar all files in a directory

    Args:
        directory: Directory path to files to tar
        tar_filename:  tar file path
    """
    with tarfile.open(tar_filename, "w") as tar_o:
        tar_o.add(directory)


def untar(directory, tar_filename):
    """Untar a tar file into a directory

    Args:
        directory: Path to directory to untar files
        tar_filename:  tar file path
    """
    with tarfile.open(tar_filename, "r") as tar_o:
        tar_o.extractall(path=directory)


def main(syn, args):
    """Run docker model"""
    if args.status == "INVALID":
        raise Exception("Docker image is invalid")

    # The new toil version doesn't seem to pull the docker config file from
    # .docker/config.json...
    # client = docker.from_env()
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    config = synapseclient.Synapse().getConfigFile(
        configPath=args.synapse_config
    )
    authen = dict(config.items("authentication"))
    client.login(username=authen['username'],
                 password=authen['password'],
                 registry="https://docker.synapse.org")

    print(getpass.getuser())

    # Create a logfile to catch stdout/stderr from the Docker runs.
    print("creating logfile")
    log_filename = args.submissionid + "_log.txt"
    open(log_filename, 'w').close()
    # warnings = []

    # Get Docker image to run and volumes to be mounted.
    docker_image = args.docker_repository + "@" + args.docker_digest
    output_dir = os.getcwd()
    # input_dir = args.input_dir

    # Pull Docker image so that the process is not included in the
    # time limit.
    print("pulling image")
    pull_docker_image(docker_image)

    # For the input directory, there will be a different case folder per
    # Docker run, e.g. /path/to/BraTS2021_00001, /path/to/BraTS2021_00013,
    # etc. In total, there will be 5 Docker runs for the validation data,
    # 500 for the testing data.
    # Need to hardcode case folder path because workflow is run in toil container
    case_folders = [
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00007",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00010",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00023",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00029",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00038",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00039",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00040",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00041",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00042",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00050",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00055",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00057",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00065",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00067",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00069",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00073",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00075",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00076",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00083",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00086",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00092",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00093",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00164",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00168",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00173",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00175",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00179",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00180",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00189",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00198",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00202",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00205",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00215",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00223",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00224",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00225",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00226",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00232",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00244",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00248",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00255",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00257",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00265",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00268",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00272",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00276",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00277",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00278",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00295",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00302",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00315",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00319",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00326",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00330",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00342",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00345",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00354",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00357",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00358",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00361",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00362",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00363",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00365",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00368",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00374",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00385",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00394",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00396",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00398",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00411",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00415",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00420",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00424",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00427",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00435",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00437",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00439",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00461",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00465",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00471",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00473",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00475",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00476",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00482",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00484",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00486",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00487",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00490",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00497",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00508",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00509",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00515",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00522",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00527",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00531",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00534",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00536",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00541",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00546",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00562",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00566",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00600",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00614",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00617",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00627",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00629",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00632",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00633",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00634",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00635",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00637",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00643",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00648",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00653",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00660",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00664",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00665",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00666",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00669",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00670",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00672",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00673",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00678",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00695",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00696",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00700",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00701",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00710",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00711",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00713",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00717",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00720",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00722",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00726",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00738",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00741",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00745",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00752",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00754",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00755",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00761",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00766",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00770",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00771",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00776",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00783",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00785",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00786",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00790",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00798",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00812",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00813",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00815",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00817",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00827",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00832",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00835",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00842",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00843",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00844",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00845",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00846",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00847",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00848",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00849",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00850",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00851",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00852",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00853",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00854",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00855",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00856",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00857",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00858",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00859",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00860",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00861",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00862",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00863",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00864",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00865",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00866",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00867",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00868",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00869",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00870",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00871",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00872",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00873",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00874",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00875",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00876",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00877",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00878",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00879",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00880",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00881",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00882",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00883",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00884",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00885",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00886",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00887",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00888",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00889",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00890",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00891",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00892",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00893",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00894",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00895",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00896",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00897",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00898",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00899",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00900",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00901",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00902",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00903",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00904",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00905",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00906",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00907",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00908",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00909",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00910",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00911",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00912",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00913",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00914",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00915",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00916",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00917",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00918",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00919",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00920",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00921",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00922",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00923",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00924",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00925",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00926",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00927",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00928",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00929",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00930",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00931",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00932",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00933",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00934",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00935",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00936",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00937",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00938",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00939",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00940",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00941",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00942",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00943",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00944",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00945",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00946",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00947",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00948",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00949",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00950",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00951",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00952",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00954",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00955",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00956",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00957",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00958",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00959",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00960",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00961",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00962",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00963",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00964",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00965",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00966",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00967",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00968",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00969",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00970",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00971",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00972",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00973",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00975",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00976",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00977",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00978",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00979",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00980",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00981",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00982",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00983",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00984",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00985",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00986",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00987",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00988",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00989",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00990",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00991",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00992",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00993",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00994",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_00995",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01799",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01800",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01801",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01802",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01803",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01804",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01805",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01806",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01807",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01808",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01809",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01810",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01811",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01812",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01813",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01814",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01815",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01816",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01817",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01818",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01819",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01820",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01821",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01822",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01823",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01824",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01825",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01826",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01827",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01828",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01829",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01830",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01831",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01832",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01833",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01834",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01835",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01836",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01837",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01838",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01839",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01840",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01841",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01842",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01843",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01844",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01845",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01846",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01847",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01848",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01849",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01850",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01851",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01852",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01853",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01854",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01855",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01856",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01857",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01858",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01859",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01860",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01861",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01862",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01863",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01864",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01865",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01866",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01867",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01868",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01869",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01870",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01871",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01872",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01873",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01874",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01875",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01876",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01877",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01878",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01879",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01880",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01881",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01882",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01883",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01884",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01885",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01886",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01887",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01888",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01889",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01890",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01891",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01892",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01893",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01894",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01895",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01896",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01897",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01898",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01899",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01900",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01901",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01902",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01903",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01904",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01905",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01906",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01907",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01908",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01909",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01910",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01911",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01912",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01913",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01914",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01915",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01916",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01917",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01918",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01919",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01920",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01921",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01922",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01923",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01924",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01925",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01926",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01927",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01928",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01929",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01930",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01931",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01932",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01933",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01934",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01935",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01936",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01937",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01938",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01939",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01940",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01941",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01942",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01943",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01944",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01945",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01946",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01947",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01948",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01949",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01950",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01951",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01952",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01953",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01954",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01955",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01956",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01957",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01958",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01959",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01960",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01961",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01962",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01963",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01964",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01965",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01966",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01967",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01968",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01969",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01970",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01971",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01972",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01973",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01974",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01975",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01976",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01977",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01978",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01979",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01980",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01981",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01982",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01983",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01984",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01985",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01986",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01987",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01988",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01989",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01990",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01991",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01992",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01993",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01994",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01995",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01996",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01997",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01998",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_01999",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02000",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02001",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02002",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02003",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02004",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02005",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02006",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02007",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02008",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02009",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02010",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02011",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02012",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02013",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02014",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02015",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02016",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02017",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02018",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02019",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02020",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02021",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02022",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02023",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02024",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02025",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02026",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02027",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02028",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02029",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02030",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02031",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02032",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02033",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02034",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02035",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02036",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02037",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02038",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02039",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02040",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02041",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02042",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02043",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02044",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02045",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02046",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02047",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02048",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02049",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02050",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02051",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02052",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02053",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02054",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02055",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02056",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02057",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02058",
        "/home/ec2-user/RSNA_ASNR_MICCAI_BraTS2021_TestingData/BraTS2021_02059"

    ]
    for case_folder in case_folders:
        # case_folder = os.path.join(input_dir, sub_dir)
        case_id = case_folder[-5:]

        print("mounting volumes")
        # Specify the input directory with 'ro' permissions, output with
        # 'rw' permissions.
        mounted_volumes = {output_dir: '/output:rw',
                           case_folder: '/input:ro'}

        # Format the mounted volumes so that Docker SDK can understand.
        all_volumes = [output_dir, case_folder]
        volumes = {}
        for vol in all_volumes:
            volumes[vol] = {'bind': mounted_volumes[vol].split(":")[0],
                            'mode': mounted_volumes[vol].split(":")[1]}

        # Run the Docker container in detached mode and with access
        # to the GPU, also making note of the start time.
        container_name = f"{args.submissionid}_case{case_id}"
        print(f"running container: {container_name}")
        # start_time = time.time()
        # time_elapsed = 0
        try:
            container = client.containers.run(docker_image,
                                              detach=True,
                                              volumes=volumes,
                                              name=container_name,
                                              network_disabled=True,
                                              stderr=True,
                                              runtime="nvidia")
        except docker.errors.APIError as err:
            container = None
            remove_docker_container(container_name)
            errors = str(err) + "\n"
        else:
            errors = ""

        # If container is running, monitor the time elapsed -- if it
        # exceeds the runtime quota, stop the container. Logs should
        # also be captured every 60 seconds.  Remove the container
        if container is not None:
            while container in client.containers.list():
                # time_elapsed = time.time() - start_time
                # if time_elapsed > args.runtime_quota:
                #     container.stop()
                #     break

                log_text = container.logs()
                create_log_file(log_filename, log_text=log_text)
                store_log_file(syn, log_filename,
                               args.parentid, store=args.store)
                time.sleep(60)

            # Note the reason for container exit in the logs if time
            # limit is reached.
            # if time_elapsed > args.runtime_quota:
            #     # TODO: uncomment for testing data
            #     # warnings.append(f"Time limit of {args.runtime_quota}s reached "
            #     #                 f"for case {case_id} - no output generated.")
            #     warnings.append(f"Time limit of {args.runtime_quota}s reached "
            #                     f"for case {case_id} - stopping submission...")
            #     container.remove()
            #     break

            # Must run again to make sure all the logs are captured
            log_text = container.logs()
            create_log_file(log_filename, log_text=log_text)
            store_log_file(syn, log_filename,
                           args.parentid, store=args.store)
            container.remove()

        statinfo = os.stat(log_filename)
        if statinfo.st_size == 0 and errors:
            create_log_file(log_filename, log_text=errors)
            store_log_file(syn, log_filename,
                           args.parentid, store=args.store)
    # if warnings:
    #     warnings_text = "\n\nWarnings:\n=========\n" + "\n".join(warnings)
    #     create_log_file(log_filename, log_text=warnings_text, mode="a")
    #     store_log_file(syn, log_filename,
    #                    args.parentid, store=args.store)

    print("finished inference")
    remove_docker_image(docker_image)

    # Check for prediction files once the Docker run is complete. Tar
    # the predictions if found; else, mark the submission as INVALID.
    if glob.glob("*.nii.gz"):
        os.mkdir("predictions")
        for nifti in glob.glob("*.nii.gz"):
            os.rename(nifti, os.path.join("predictions", nifti))
        tar("predictions", "predictions.tar.gz")
        status = "VALIDATED"
        invalid_reasons = ""
    else:
        status = "INVALID"
        invalid_reasons = (
            "No *.nii.gz files found; please check whether running the "
            "Docker container locally will result in a NIfTI file within "
            "the time constaint."
        )
    with open("results.json", "w") as out:
        out.write(json.dumps(
            {
                "submission_status": status,
                "submission_errors": invalid_reasons
            }
        ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--submissionid", required=True,
                        help="Submission Id")
    parser.add_argument("-p", "--docker_repository", required=True,
                        help="Docker Repository")
    parser.add_argument("-d", "--docker_digest", required=True,
                        help="Docker Digest")
    parser.add_argument("-i", "--input_dir", required=True,
                        help="Input Directory")
    parser.add_argument("-c", "--synapse_config", required=True,
                        help="credentials file")
    # parser.add_argument("-rt", "--runtime_quota",
    #                     help="runtime quota in seconds", type=int)
    parser.add_argument("--store", action='store_true',
                        help="to store logs")
    parser.add_argument("--parentid", required=True,
                        help="Parent Id of submitter directory")
    parser.add_argument("--status", required=True, help="Docker image status")
    args = parser.parse_args()
    syn = synapseclient.Synapse(configPath=args.synapse_config)
    syn.login(silent=True)
    main(syn, args)
