#!/usr/bin/env bash

# 5-bit quantised models that run across the two respective RTX 3090s
llama-server -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q5_K_S -t 4 -dev CUDA0,CUDA1 -sm none -mg 0 &>/dev/null &

# 3-bit quantised model that runs on the RTX 4060 Ti (16 GB)
llama-server -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q3_K_M -t 4 -dev CUDA2 -sm none -mg 0 --port 8081 &>/dev/null &
