#!/usr/bin/env bash

builder_devices=0,2 # i.e. first RTX 3090 and the 4060
reviewer_devices=1 # i.e. Second RTX 3090

# 5-bit quantised model that run across the first 3090 and 4060
# A split ratio of '0.5,0.5' forces the KV cache and layers
# to span evenly across both logical IDs.
#
# Context keys and values are 8-bit quantised namely to allow llama-server
# to allocate KV cache on first builder GPU before applying the tensor split.
CUDA_VISIBLE_DEVICES=$builder_devices llama-server \
    -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q5_K_S \
    -t 4 \
    -ngl 48 \
    -ts 0.5,0.5 \
    -c 115000 \
    -ctk q8_0 \
    -ctv q8_0 \
    -fa 1 \
    -n 4096 \
    --port 8080 &>/dev/null &

# 3-bit quantised model that runs on the second 3090
CUDA_VISIBLE_DEVICES=$reviewer_devices llama-server \
    -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q3_K_M \
    -t 4 \
    -ctk q8_0 \
    -ctv q8_0 \
    --port 8081 &>/dev/null &
