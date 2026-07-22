#!/usr/bin/env bash

builder_devices=0,2 # i.e. both RTX 3090s
reviewer_devices=1 # i.e. RTX 4060 Ti

# 5-bit quantised models that run across the two respective RTX 3090s
# This is explicitly configured to host the weights on the first RTX 3090,
# leaving the second 3090 to serve as storage for the context window.
#
# Context keys and values are 8-bit quantised namely to allow llama-server
# to allocate KV cache on first builder GPU before applying the tensor split.
CUDA_VISIBLE_DEVICES=$builder_devices llama-server \
    -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q5_K_S \
    -t 4 \
    -ngl 48 \
    -ts 1,0 \
    -c 64000 \
    -ctk q8_0 \
    -ctv q8_0 \
    -fa 1 \
    -n 4096 &>/dev/null &

# 3-bit quantised model that runs on the RTX 4060 Ti (16 GB)
CUDA_VISIBLE_DEVICES=$reviewer_devices llama-server \
    -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q3_K_M \
    -t 4 \
    --port 8081 &>/dev/null &
