#!/bin/bash
cd ~/MiClaw-AI-Blog/articles
for f in *.md; do
  if ! head -1 "$f" | grep -q '^---'; then
    title=$(head -1 "$f" | sed 's/#* //' | sed 's/^[[:space:]]*//')
    date=$(echo "$f" | grep -oP '\d{4}-\d{2}-\d{2}')
    tmp=$(mktemp)
    echo "---" > "$tmp"
    echo "title: \"$title\"" >> "$tmp"
    echo "date: $date" >> "$tmp"
    echo "layout: post" >> "$tmp"
    echo "---" >> "$tmp"
    echo "" >> "$tmp"
    cat "$f" >> "$tmp"
    mv "$tmp" "$f"
    echo "Done: $f"
  fi
done