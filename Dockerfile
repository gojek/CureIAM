FROM python:3.7.11-alpine3.14

RUN mkdir -p /usr/app/cureiam

# Create user
ENV USER=cureiam
ENV UID=1001

RUN addgroup cureiam

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "$(pwd)" \
    --ingroup "$USER" \
    --no-create-home \
    --uid "$UID" \
    "$USER"

# Change workdir
WORKDIR /usr/app/cureiam

# Copy the necessary files
COPY CureIAM CureIAM
COPY requirements.txt requirements.txt
COPY CureIAM.yaml CureIAM.yaml
COPY cureiamSA.json cureiamSA.json

# make cureiam user the owner of /usr/app/cureiam
RUN chown -R cureiam:cureiam /usr/app/cureiam

# Install deps
RUN pip install -r requirements.txt

# Set user
USER cureiam

ENTRYPOINT ["python"]
CMD ["-m", "CureIAM"]
