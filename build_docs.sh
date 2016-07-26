#! /bin/sh

mkdir -p docs

for module in chainz chainz.Chain chainz.utils; do
  pydoc $module > docs/${module}.txt
done

pandoc -o README.rst README.md
