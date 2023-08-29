#!/bin/env python3

import re
import subprocess
import sys

def increasePatch(match_obj):
    patch = int(match_obj.group(2))
    return match_obj.group(1) + str(patch + 1) + match_obj.group(3)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} [main branch]")
        sys.exit(1)

    print(f"Comparing to branch {sys.argv[1]}")
    result = subprocess.run(["git", "diff", "--name-only", "--diff-filter=ACM", sys.argv[1]], stdout = subprocess.PIPE, text = True, check = True)
    files = [f for f in result.stdout.split("\n") if f.lower().endswith(".xml")] # Filter out XML files only
    print(f"Found {len(files)} files:")

    version_re = re.compile("(<\s*version\s+value\s*=\s*[\"'][0-9]+\.[0-9]+\.)([0-9]+)([\"']\s*/>)")

    for file_path in files:
        content = open(file_path, "r", newline = '').read()
        new_content, num_replacements = version_re.subn(increasePatch, content)
        if num_replacements == 0:
            print(f"nothing to do: {file_path}")
        else:
            with open(file_path, "w+", newline = '') as f:
                f.write(new_content)
            if num_replacements == 1:
                print(f"done: {file_path}")
            else:
                print(f"WARNING: more than one replacement: {file_path}")
