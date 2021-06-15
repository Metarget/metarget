FROM ubuntu

RUN apt-get update && apt-get install net-tools -y
COPY poc /
RUN chmod a+x poc

CMD /bin/bash
