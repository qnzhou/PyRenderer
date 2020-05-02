FROM pymesh/pymesh:py2.7-slim
WORKDIR /root/

RUN apt-get update && apt-get install -y scons libboost-all-dev libxerces-c-dev libeigen3-dev \
libglu1-mesa-dev libglewmx1.5-dev libfftw3-dev libopenexr-dev libxxf86vm-dev && \
pip install PyOpenGL mako && \
git clone https://github.com/qnzhou/mitsuba.git && \
cp mitsuba/build/config-linux-gcc.py mitsuba/config.py

WORKDIR mitsuba
RUN python2 $(which scons)

WORKDIR /root/
RUN mv /root/mitsuba /usr/local/.
RUN chgrp -R staff /usr/local/mitsuba
RUN echo ". /usr/local/mitsuba/setpath.sh" >> /etc/bash.bashrc

WORKDIR /root/
git clone https://github.com/qnzhou/PyRenderer.git
# COPY . PyRenderer
RUN mv /root/PyRenderer /usr/local/.
RUN chgrp -R staff /usr/local/PyRenderer
ENV PATH "/usr/local/PyRenderer/:$PATH"
