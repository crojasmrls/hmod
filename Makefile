default: run-all
.PHONY: default

BASE_DIR ?= $(abspath .)
PYTHON ?= python

#RISCV BENCHMARKS REPOSITORY Variables
RISCV_CEXAMPLES ?= $(BASE_DIR)/risc-v-examples/c_implementations
bmarks ?=        \
	bubblesort	\
	counters	\
	matrix_mul	\
	spmv	\
# RISCV ASM targets
bmarks_riscv_asm  = $(addprefix $(RISCV_CEXAMPLES)/, $(addsuffix .s, $(bmarks)))
$(bmarks_riscv_asm): $(RISCV_CEXAMPLES)/%.s: $(RISCV_CEXAMPLES)/%/ $(wildcard $(RISCV_CEXAMPLES)/common/*)
	$(MAKE) -C $(RISCV_CEXAMPLES) $(notdir $@)

## HMOD variables
MAIN_PY ?= $(BASE_DIR)/src/read-pseudocode.py
OUT_DIR ?= $(BASE_DIR)/outputs
LOG_DIR ?= $(OUT_DIR)/logs
MAX_CYCLES ?= 400000
FLAGS_PY ?= -k -t -m -c $(MAX_CYCLES)

python_logs  = $(addprefix $(LOG_DIR)/, $(addsuffix .log, $(bmarks)))
$(python_logs): $(LOG_DIR)/%.log: $(RISCV_CEXAMPLES)/%.s
	mkdir -p $(dir $@)
	$(PYTHON) $(MAIN_PY) $(FLAGS_PY) -o $(OUT_DIR)/$* -s $(RISCV_CEXAMPLES)/$*.s &> $@
junk+=$(python_logs)

run-all: $(python_logs)
clean:
	rm -rf $(junk)
.PHONY: default run-all clean test
