default: run-all
.PHONY: default

BASE_DIR ?= $(abspath .)
PYTHON ?= python3

#RISCV BENCHMARKS REPOSITORY Variables
RISCV_CEXAMPLES ?= $(BASE_DIR)/risc-v-examples/c_implementations
bmarks =        \
	int-matmul \
	int-vvadd \
	fp-matmul \
	fp-vvadd \
	int-spmv \
	fp-spmv \
	histogram \
	rsort \
	int-qsort \
	int-bsort \
	fp-qsort \
	fp-bsort \
	int-median \
	fp-median \
	fibonacci \
	towers \
	#counters	\

# RISCV ASM targets
bmarks_riscv_asm  = $(addprefix $(RISCV_CEXAMPLES)/, $(addsuffix .s, $(bmarks)))
$(bmarks_riscv_asm): $(RISCV_CEXAMPLES)/%.s: $(RISCV_CEXAMPLES)/%/ $(wildcard $(RISCV_CEXAMPLES)/common/*)
	$(MAKE) -C $(RISCV_CEXAMPLES) bmarks=$(notdir $(basename $@))

## HMOD variables
SRCS_PY ?= $(BASE_DIR)/src
MAIN_PY ?= $(SRCS_PY)/read-pseudocode.py
DEPS_PY = $(wildcard $(SRCS_PY)/*.py)
OUT_DIR ?= $(BASE_DIR)/outputs
LOG_DIR ?= $(OUT_DIR)/logs
MAX_CYCLES ?= 10000000
FLAGS_PY ?= -k -t -m -c $(MAX_CYCLES)
FLAGS_PY_ATM ?= -a -t --Tracer_name atm_torture_signature.sig

#HMOD run
python_logs  = $(addprefix $(LOG_DIR)/, $(addsuffix .log, $(bmarks)))
$(python_logs): $(LOG_DIR)/%.log: $(RISCV_CEXAMPLES)/%.s $(DEPS_PY)
	mkdir -p $(dir $@)
	time $(PYTHON) $(MAIN_PY) $(FLAGS_PY) -o $(OUT_DIR)/$* -s $(RISCV_CEXAMPLES)/$*.s > $@
	@(echo "$(notdir $(basename $@)) finished")
junk+=$(python_logs)

#HMOD atomic model
python_logs_atm = $(addprefix $(LOG_DIR)_atm/, $(addsuffix .log, $(bmarks)))

$(python_logs_atm): $(LOG_DIR)_atm/%.log: $(RISCV_CEXAMPLES)/%.s $(DEPS_PY)
	mkdir -p $(dir $@)
	time $(PYTHON) $(MAIN_PY) $(FLAGS_PY_ATM) -o $(OUT_DIR)/$* -s $(RISCV_CEXAMPLES)/$*.s > $@
	@(echo "$(notdir $(basename $@)) finished")
junk+=$(python_logs_atm)

perf_model: $(python_logs)
atm_model: $(python_logs_atm)

$(bmarks): %: $(LOG_DIR)/%.log
$(addsuffix _atm, $(bmarks)): %_atm: $(LOG_DIR)_atm/%.log

run-all: $(python_logs) $(python_logs_atm)
clean:
	rm -rf $(junk)
.PHONY: default run-all clean test perf_model atm_model $(bmarks) $(addsuffix _atm, $(bmarks))
