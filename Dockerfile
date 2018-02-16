FROM qnzhou/pymesh
WORKDIR /root/

RUN apt-get install -y scons libboost-all-dev libxerces-c-dev libeigen3-dev \
python-opengl libglu1-mesa-dev libglewmx1.5-dev libfftw3-dev libopenexr-dev python3-mako && \
git clone https://github.com/qnzhou/mitsuba.git && \
cp mitsuba/build/config-docker.py mitsuba/config.py && \
git clone https://github.com/qnzhou/PyRenderer.git


WORKDIR mitsuba
RUN scons
WORKDIR /root/
RUN echo ". /root/mitsuba/setpath.sh" >> /root/.bashrc
ENV PATH "/root/PyRenderer/:$PATH"
ENTRYPOINT bash

