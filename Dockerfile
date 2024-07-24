FROM ubuntu:24.04
RUN apt-get update && apt-get install -y device-tree-compiler libboost-system-dev \
    libboost-regex-dev autoconf automake autotools-dev curl python3 \
    python3-pip libmpc-dev libmpfr-dev libgmp-dev gawk build-essential \
    bison flex texinfo gperf libtool patchutils bc zlib1g-dev \
    libexpat-dev ninja-build git cmake libglib2.0-dev libslirp-dev time python3-pip
RUN python3 -m pip install salabim pycachesim --break-system-packages
WORKDIR /usr/local/tmp
RUN git clone https://github.com/riscv-collab/riscv-gnu-toolchain.git --branch=2024.04.12 && \
cd riscv-gnu-toolchain && \
./configure && \
make -j$(nproc) && make linux -j$(nproc) && \
git submodule update --init --recursive spike && \
cd spike && mkdir build && \
cd build && \
../configure && \
make -j$(nproc) && make install && \
cd ../../ && \
 git submodule update --init --recursive pk && \
cd pk && mkdir build && cd build && \
../configure --host=riscv64-unknown-elf --with-arch=rv64gc_zifencei && \
make -j$(nproc) && make install && \
cd ../../ && \
rm -rf riscv-gnu-toolchain
WORKDIR /
