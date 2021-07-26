FROM cbica/captk:release-1.8.1

# Download nibabel package for validation
RUN pip install nibabel

COPY validate.py /usr/local/bin/.
COPY score.py /usr/local/bin/.

# Override the base image's entrypoint so that the GUI does
# not start when the container is run
ENTRYPOINT ["/usr/bin/env"]
