FROM python:3.7.11-alpine3.14

# For seting up the timezone
ENV TZ=Asia/Kolkata
RUN apk update && apk add tzdata

# Create user
ENV USER=cureiam
ENV UID=1001

RUN addgroup cureiam

RUN adduser \
    --disabled-password \
    --gecos "" \
    --ingroup "$USER" \
    --uid "$UID" \
    "$USER"

# Change workdir
WORKDIR /home/cureiam

# Copy the necessary files
COPY CureIAM CureIAM
COPY requirements.txt requirements.txt
COPY CureIAM.yaml CureIAM.yaml
COPY cureiamSA.json cureiamSA.json


# Set user
USER cureiam

# Install deps
RUN export PATH=$PATH:/home/cureiam/.local/bin
RUN pip install -r requirements.txt --no-warn-script-location

ENTRYPOINT ["python"]
CMD ["-m", "CureIAM"]
