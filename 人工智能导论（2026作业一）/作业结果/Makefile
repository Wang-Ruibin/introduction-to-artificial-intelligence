CXX ?= g++
CXXFLAGS := -std=c++20 -O3 -Wall -Wextra -Wpedantic
SRC := src/cpp
BUILD := build
.PHONY: all test run clean
all: $(BUILD)/tsp_metaheuristics
$(BUILD):
	mkdir -p $(BUILD)
$(BUILD)/tsp_metaheuristics: $(SRC)/main.cpp $(SRC)/tsp.cpp $(SRC)/ga.cpp $(SRC)/aco.cpp | $(BUILD)
	$(CXX) $(CXXFLAGS) $^ -o $@
$(BUILD)/tests: $(SRC)/tests.cpp $(SRC)/tsp.cpp | $(BUILD)
	$(CXX) $(CXXFLAGS) $^ -o $@
test: $(BUILD)/tests
	./$(BUILD)/tests
run: all
	python3 src/run_experiments.py
clean:
	rm -rf $(BUILD)
