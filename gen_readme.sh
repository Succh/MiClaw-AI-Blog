#!/bin/bash
cd /data/data/com.termux/files/home/MiClaw-AI-Blog/articles
for f in $(ls *.md 2>/dev/null | sort); do
  title=$(awk '/^title:/{gsub(/^title: *"*/,""); gsub(/"*$/,"",$0); print; exit}' "$f" 2>/dev/null)
  if [ -z "$title" ]; then
    title=$(echo "$f" | sed 's/^[0-9-]*//;s/\.md$//;s/-/ /g')
  fi
  echo "$f|$title"
done
