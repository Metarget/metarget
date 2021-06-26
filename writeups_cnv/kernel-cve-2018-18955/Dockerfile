FROM ubuntu

RUN apt-get update && apt-get install uidmap -y
RUN useradd -u 1001 poc
COPY subshell /
COPY subuid_shell /

USER 1001

CMD /bin/bash
