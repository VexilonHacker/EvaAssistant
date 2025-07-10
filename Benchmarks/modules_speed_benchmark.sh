#!/bin/bash

# Output file
RESULTS_FILE="ollama_benchmark_results.txt"
echo "=== OLLAMA MODEL BENCHMARK ===" > "$RESULTS_FILE"
echo "Benchmark started at: $(date)" >> "$RESULTS_FILE"
echo >> "$RESULTS_FILE"

# List of model names exactly as pulled into Ollama
MODELS=("tinydolphin" "gurubot/phi3-mini-abliterated" "huihui_ai/phi4-mini-abliterated" "gemma3")

# Questions to benchmark
QUESTIONS=(
  "Explain quantum entanglement in simple terms."
  "How does a neural network learn?"
  "Why is the sky blue?"
)

# Display info
echo "Models: ${MODELS[*]}"
echo "Number of questions: ${#QUESTIONS[@]}"
echo

# Iterate through questions
for i in "${!QUESTIONS[@]}"; do
    QUESTION="${QUESTIONS[$i]}"
    echo "==============================="
    echo "Question $((i+1)): $QUESTION"
    echo "==============================="

    echo "### Question $((i+1)): $QUESTION" >> "$RESULTS_FILE"
    echo >> "$RESULTS_FILE"

    for MODEL in "${MODELS[@]}"; do
        echo "----- Model: $MODEL -----"
        echo "## Model: $MODEL" >> "$RESULTS_FILE"
        echo "Timestamp: $(date)" >> "$RESULTS_FILE"

        START=$(date +%s.%N)
        RESPONSE=$(ollama run "$MODEL" "$QUESTION" 2>&1)
        END=$(date +%s.%N)

        RUNTIME=$(echo "$END - $START" | bc)
        echo "Execution time: ${RUNTIME}s"
        echo "Execution time: ${RUNTIME}s" >> "$RESULTS_FILE"

        echo "Response:" >> "$RESULTS_FILE"
        echo "$RESPONSE" >> "$RESULTS_FILE"
        echo "--------------------------" >> "$RESULTS_FILE"
        echo >> "$RESULTS_FILE"
    done
    echo >> "$RESULTS_FILE"
done

echo "Benchmark complete! Results saved to: $RESULTS_FILE"
