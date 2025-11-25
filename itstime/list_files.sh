#!/bin/bash
# Quick reference to list generated TTS files

echo "=== Time TTS Files by Language ==="
echo ""

for lang in hu en it de es; do
    echo "--- ${lang^^} (${lang}) ---"
    ls -1 *_${lang}.mp3 2>/dev/null | sort | sed 's/_'${lang}'.mp3//' | while read time; do
        echo "  ${time:0:2}:${time:2:2}"
    done
    echo ""
done

echo "=== Statistics ==="
echo "Total files: $(ls -1 *.mp3 2>/dev/null | wc -l)"
for lang in hu en it de es; do
    count=$(ls -1 *_${lang}.mp3 2>/dev/null | wc -l)
    echo "${lang^^}: $count files"
done
