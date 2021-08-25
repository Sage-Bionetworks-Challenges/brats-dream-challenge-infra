"""Run training synthetic docker models"""
from __future__ import print_function
import argparse
import getpass
import os
import tarfile
import time
import glob

import docker
import synapseclient


def create_log_file(log_filename, log_text=None):
    """Create log file"""
    with open(log_filename, 'w') as log_file:
        if log_text is not None:
            if isinstance(log_text, bytes):
                log_text = log_text.decode("utf-8")
            log_file.write(log_text.encode("ascii", "ignore").decode("ascii"))
        else:
            log_file.write("No Logs")


def store_log_file(syn, log_filename, parentid, store=True):
    """Store log file"""
    statinfo = os.stat(log_filename)
    if statinfo.st_size > 0 and statinfo.st_size/1000.0 <= 50:
        ent = synapseclient.File(log_filename, parent=parentid)
        if not store:
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
    # TODO: Potentially add code to remove all files that were zipped.


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
    # dockercfg_path=".docker/config.json")

    print(getpass.getuser())

    # Add docker.config file
    docker_image = args.docker_repository + "@" + args.docker_digest

    # These are the volumes that you want to mount onto your docker container
    #output_dir = os.path.join(os.getcwd(), "output")
    output_dir = os.getcwd()
    input_dir = args.input_dir

    for root, sub_dirs, _ in os.walk(input_dir):
        for sub_dir in sub_dirs:
            case_folder = os.path.join(root, sub_dir)
            case_id = case_folder[-5:]

            print("mounting volumes")
            # These are the locations on the docker that you want your mounted
            # volumes to be + permissions in docker (ro, rw)
            # It has to be in this format '/output:rw'
            mounted_volumes = {output_dir: '/output:rw',
                               case_folder: '/input:ro'}
            # All mounted volumes here in a list
            all_volumes = [output_dir, case_folder]
            # Mount volumes
            volumes = {}
            for vol in all_volumes:
                volumes[vol] = {'bind': mounted_volumes[vol].split(":")[0],
                                'mode': mounted_volumes[vol].split(":")[1]}

            # Look for if the container exists already, if so, reconnect
            print("checking for containers")
            container = None
            errors = None
            for cont in client.containers.list(all=True):
                if args.submissionid in cont.name:
                    # Must remove container if the container wasn't killed properly
                    if cont.status == "exited":
                        cont.remove()
                    else:
                        container = cont
            # If the container doesn't exist, make sure to run the docker image
            if container is None:
                # Run as detached, logs will stream below
                print("running container")
                start_time = time.time()
                time_elapsed = 0
                try:
                    container = client.containers.run(docker_image,
                                                      detach=True, 
                                                      volumes=volumes,
                                                      name=args.submissionid,
                                                      network_disabled=True,
                                                      stderr=True,
                                                      runtime="nvidia")
                except docker.errors.APIError as err:
                    remove_docker_container(args.submissionid)
                    errors = str(err) + "\n"

            print("creating logfile")
            # Create the logfile
            log_filename = args.submissionid + "_log.txt"
            # Open log file first
            open(log_filename, 'w').close()

            # If the container doesn't exist, there are no logs to write out and
            # no container to remove
            if container is not None:
                # Check if container is still running
                while container in client.containers.list():

                    # Check the elapsed time for the docker run; if over the
                    # runtime quota, stop the container.
                    time_elapsed = time.time() - start_time
                    if time_elapsed > args.runtime_quota:
                        container.stop()
                        break

                    log_text = container.logs()
                    create_log_file(log_filename, log_text=log_text)
                    store_log_file(syn, log_filename,
                                   args.parentid, store=args.store)
                    time.sleep(60)

                # Note the reason for container exit in the logs if time
                # limit is reached.
                if time_elapsed > args.runtime_quota:
                    log_text = (f"Time limit of {args.runtime_quota}s reached"
                                f"for case {case_id} - no output generated.")

                else:
                    # Must run again to make sure all the logs are captured
                    log_text = container.logs()

                create_log_file(log_filename, log_text=log_text)
                store_log_file(syn, log_filename,
                               args.parentid, store=args.store)
                # Remove container and image after being done
                container.remove()

            statinfo = os.stat(log_filename)

            if statinfo.st_size == 0:
                create_log_file(log_filename, log_text=errors)
                store_log_file(syn, log_filename,
                               args.parentid, store=args.store)

    print("finished training")
    # Try to remove the image
    remove_docker_image(docker_image)

    if not glob.glob("*.nii.gz"):
        raise Exception(
            "No *.nii.gz files found; please check whether running the Docker "
            "container locally will result in a NIfTI file."
        )

    # Create directory of prediction files to tar.
    os.mkdir(f"predictions")
    for nifti in glob.glob("*.nii.gz"):
        os.rename(nifti, os.path.join("predictions", nifti))
    tar("predictions", "predictions.tar.gz")


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
    parser.add_argument("-rt", "--runtime_quota",
                        help="runtime quota in seconds")
    parser.add_argument("--store", action='store_true',
                        help="to store logs")
    parser.add_argument("--parentid", required=True,
                        help="Parent Id of submitter directory")
    parser.add_argument("--status", required=True, help="Docker image status")
    args = parser.parse_args()
    syn = synapseclient.Synapse(configPath=args.synapse_config)
    syn.login()
    main(syn, args)
