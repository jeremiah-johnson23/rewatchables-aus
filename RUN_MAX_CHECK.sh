#!/bin/bash

# HBO Max / Max Streaming Availability Checker
# This script checks all 423 movies against JustWatch Australia

echo "======================================"
echo "Max Streaming Availability Checker"
echo "======================================"
echo ""
echo "This will check all 423 movies in episodes.json"
echo "against JustWatch Australia to find Max availability."
echo ""
echo "Estimated time: 5-7 minutes"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

echo ""
echo "Starting check..."
echo ""

# Run the Node.js script
# - Progress goes to stderr (displayed on screen)
# - Episode IDs go to stdout (saved to file)
node check-max-streaming.js > max-episode-ids.json 2>&1

# Check if it succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ CHECK COMPLETE!"
    echo "======================================"
    echo ""
    echo "Results saved to:"
    echo "  - max-episode-ids.json (Episode IDs with Max)"
    echo "  - max-availability-results.json (Full details)"
    echo ""
    echo "To view the episode IDs:"
    echo "  cat max-episode-ids.json"
    echo ""
    echo "To view full results:"
    echo "  cat max-availability-results.json | jq '.[] | select(.hasMax==true)'"
    echo ""
else
    echo ""
    echo "======================================"
    echo "✗ CHECK FAILED"
    echo "======================================"
    echo ""
    echo "Check the error messages above."
    exit 1
fi
