<h2 align="center">HMOD a High-level microarchitecture modeling tool</h2>

<p align="center">
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

_HMOD_ is a simulator implemented in Python that permits the implementation and evaluation of different microarchitecture models with an agile approach to speed up the design exploration space in the first stages of the microarchitecture design.

## Installation and usage

### Installation

_HMOD_ relies on the [Salabim simulator](https://www.salabim.org/) to manage dependencies and resources to model the different microarchitectures. Salabim can be installed by running `pip install salabim`. Also, as cache replacement model it uses the [Python Cache Hierarchy Simulator](https://pypi.org/project/pycachesim/) that can be installed by running `pip install pycachesim`

Additionally, you will need the RISC-V toolchain to compile C code and obtain RISC-V assembly. Follow the instructions on the risc-v-examples submodule or use a docker image as indicated below.

#### Docker Images
Install docker:

    sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

Check if Docker daemon is running:

    sudo systemctl is-active docker

If not, activate it:

    sudo systemctl start docker

For building a Docker image that contains the risc-v tools, you can use the included docker file.

    sudo docker build -t hmod_env .

Alternatively, you can download the following docker image from the docker hub.

    sudo docker pull docker.io/crojasmrls/hmod_env

When you have the image ready, you can create a new container using this command:

    sudo docker run -it --mount src=$(pwd),target=/hmod,type=bind hmod_env
    cd hmod

### Usage

For executing a simulation, it is necessary to run the main file `read-pseudocode.py`; in this file, you can specify which parameters to use, the simulated time, and the assembly code to run.

## Key features.
### v1.0.0
- Execute assembly programs
- [RISC-V unprivileged ISA](https://github.com/riscv/riscv-isa-manual/releases/download/Ratified-IMAFDQC/riscv-spec-20191213.pdf) subset
- Out-of-order parametrizable pipeline model
- IPC counter
- [Konata](https://github.com/shioyadan/Konata) tracer Support

## Authors

See [AUTHORS.md](./AUTHORS.md)

## Code of Conduct

Everyone participating in the _HMOD_ project, and in particular in the issue tracker, pull requests, and social media activity, is expected to treat other people with respect and, more generally, to follow the guidelines articulated in the [Python Community Code of Conduct](https://www.python.org/psf/codeofconduct/).
