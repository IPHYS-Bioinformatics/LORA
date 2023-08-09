FROM python:3.10-slim AS python-venv-image

# install git required for dash installation
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt update && \
        apt -y install git

# set the environment variable where the venv should be created
ENV VIRTUAL_ENV=/opt/venv

# create the venv
RUN python -m venv $VIRTUAL_ENV
# prepend our virtual environment to the PATH so our stuff takes precedence over defaults in the system
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# copy the requirements
COPY requirements-linux.txt requirements.txt

# install the requirements
RUN pip install -r requirements.txt

# Second Image to only copy the venv dependencies over
FROM python:3.10-slim AS build-image

# copy the venv dependencies
COPY --from=python-venv-image /opt/venv /opt/venv

# install JRE for Java 17, skip stuff like documentation, clean up the apt cache
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt update && \
        apt -y install --no-install-recommends openjdk-17-jre-headless && \
	rm -rf /var/lib/apt/lists/* 

# create an app directory
RUN mkdir /lora

# copy src contents to app directory
COPY ./src/ /lora/

# set the working directory for next steps
WORKDIR /lora/

# expose the port to the outside
EXPOSE 8050

# prepend our virtual environment to the PATH so our stuff takes precedence over defaults in the system
ENV PATH="/opt/venv/bin:$PATH"

# run the main script to start in WORKDIR
CMD ["python", "index.py"]
