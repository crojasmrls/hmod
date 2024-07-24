FROM fedora:39
RUN dnf update -y && dnf install -y autoconf automake python3 libmpc-devel mpfr-devel \
gmp-devel gawk bison flex texinfo patchutils gcc gcc-c++ zlib-devel expat-devel \
libslirp-devel dtc time python3-pip python3-devel git diffutils
RUN python3 -m pip install salabim pycachesim
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
