FROM cbica/captk:release-1.8.1

RUN yum install -y xz-devel
RUN pip install --upgrade pip
RUN pip install pandas synapseclient nibabel

COPY utils.py /usr/local/bin/.
COPY validate.py /usr/local/bin/.
COPY score.py /usr/local/bin/.

# Manually copy the Hausdorff binary, as an NITRC issue is
# preventing some of the precompiled apps from getting pushed
COPY Hausdorff95 /work/CaPTk/bin/.

# Override the base image's entrypoint so that the GUI does
# not start when the container is run
ENTRYPOINT ["/usr/bin/env"]
