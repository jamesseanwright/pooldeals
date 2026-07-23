#!/usr/bin/env bash

builder_devices=CUDA0,CUDA1
reviewer_devices=CUDA2

# 5-bit quantised model that run across both 3090s
# A split ratio of '0.5,0.5' forces the KV cache and layers
# to span evenly across both logical IDs.
#
# Context keys and values are 8-bit quantised namely to allow llama-server
# to allocate KV cache on first builder GPU before applying the tensor split.
llama-server \
    -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q5_K_S \
    -t 4 \
    -dev $builder_devices \
    -ngl 48 \
    -ts 0.5,0.5 \
    -c 280000 \
    -ctk q8_0 \
    -ctv q8_0 \
    -fa 1 \
    -n 4096 \
    --port 8080 &>/dev/null &

# 3-bit quantised model that runs on the 4060 (16 GB)
llama-server \
    -hf unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q3_K_M \
    -t 4 \
    -dev $reviewer_devices \
    -ctk q8_0 \
    -ctv q8_0 \
    --port 8081 &>/dev/null &
