#!/bin/bash

MAX_ITERATIONS=${1:-15}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting Ralph for Rust Trading Bot"
echo "📍 Working directory: $PROJECT_ROOT"
echo "🔄 Max iterations: $MAX_ITERATIONS"
echo ""

for i in $(seq 1 $MAX_ITERATIONS); do
  echo "═══════════════════════════════════════"
  echo "🔄 Iteration $i of $MAX_ITERATIONS"
  echo "═══════════════════════════════════════"
  echo ""
  
  # Check if all stories are complete
  INCOMPLETE=$(cat "$SCRIPT_DIR/prd.json" | grep '"passes": false' | wc -l | tr -d ' ')
  if [ "$INCOMPLETE" -eq "0" ]; then
    echo "✅ Ralph completed successfully!"
    echo "🎉 All user stories are done"
    exit 0
  fi
  
  echo "📊 Stories remaining: $INCOMPLETE"
  echo "🤖 Starting iteration..."
  echo ""
  
  # Run the agent with the prompt
  cd "$PROJECT_ROOT"
  
  # Run claude in background with a timeout mechanism
  (
    yes "" | head -20 | cat "$SCRIPT_DIR/prompt.md" - | claude --dangerously-skip-permissions 2>&1
  ) &
  CLAUDE_PID=$!
  
  # Wait for claude with timeout (60 seconds)
  TIMEOUT=60
  ELAPSED=0
  while kill -0 $CLAUDE_PID 2>/dev/null; do
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    if [ $ELAPSED -ge $TIMEOUT ]; then
      echo "⏱️  Claude timed out after ${TIMEOUT}s - killing process"
      kill -9 $CLAUDE_PID 2>/dev/null
      break
    fi
  done
  
  # Wait for process to fully exit
  wait $CLAUDE_PID 2>/dev/null || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ] && [ $EXIT_CODE -ne 141 ] && [ $EXIT_CODE -ne 143 ]; then
      echo "⚠️  Claude exited with code $EXIT_CODE"
    fi
  }
  
  echo ""
  echo "✅ Iteration $i complete"
  echo "⏸️  Pausing 5 seconds before next iteration..."
  echo ""
  sleep 5
done

echo ""
echo "⚠️  Max iterations reached ($MAX_ITERATIONS)"
echo "📊 Check progress.txt for status"

# Check final status
INCOMPLETE=$(cat "$SCRIPT_DIR/prd.json" | grep '"passes": false' | wc -l | tr -d ' ')
echo "📊 Stories remaining: $INCOMPLETE"
exit 1
