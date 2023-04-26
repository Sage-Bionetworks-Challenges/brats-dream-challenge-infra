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

    # Get Docker image to run and volumes to be mounted.
    docker_image = args.docker_repository + "@" + args.docker_digest

    # Pull Docker image so that the process is not included in the
    # time limit.
    pull_docker_image(docker_image)

    print("mounting volumes")
    input_dir = args.input_dir
    model_dir = os.path.join(os.getcwd(), "model")
    mounted_volumes = {input_dir: '/input:ro',
                       model_dir: '/model:z'}

    # Format the mounted volumes so that Docker SDK can understand.
    all_volumes = [input_dir, model_dir]
    volumes = {}
    for vol in all_volumes:
        volumes[vol] = {'bind': mounted_volumes[vol].split(":")[0],
                        'mode': mounted_volumes[vol].split(":")[1]}

    # Run the Docker container in detached mode and with access
    # to the GPU.
    container_name = args.submissionid
    try:
        container = client.containers.run(docker_image,\
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

    # Capture logs every 60 seconds. Remove the container when done.
    if container is not None:
        while container in client.containers.list():
            log_text = container.logs(timestamps=True)
            create_log_file(log_filename, log_text=log_text)
            store_log_file(syn,
                           log_filename,
                           args.parentid)
            time.sleep(60)

        # Must run again to make sure all the logs are captured
        log_text = container.logs(timestamps=True)
        create_log_file(log_filename, log_text=log_text)
        store_log_file(syn,
                       log_filename,
                       args.parentid)
        container.remove()

    statinfo = os.stat(log_filename)
    if statinfo.st_size == 0 and errors:
        create_log_file(log_filename, log_text=errors)
        store_log_file(syn,
                       log_filename,
                       args.parentid)

    print("finished training")
    remove_docker_image(docker_image)

    list_model = os.listdir(model_dir)
    if not list_model:
        model_fill = os.path.join(model_dir, "model_fill.txt")
        open(model_fill, 'w').close()
        # raise Exception("No model generated, please check training docker")
    tar(model_dir, 'model_files.tar.gz')


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
    parser.add_argument("--parentid", required=True,
                        help="Parent Id of submitter directory")
    parser.add_argument("--status", required=True, help="Docker image status")
    args = parser.parse_args()
    syn = synapseclient.Synapse(configPath=args.synapse_config)
    syn.login(silent=True)
    main(syn, args)
