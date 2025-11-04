import difflib

def compare_texts(text1: str, text2: str) -> dict:
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    d = difflib.ndiff(lines1, lines2)
    added = [line[2:] for line in d if line.startswith("+ ") and not any(removed_line[2:] == line[2:] for removed_line in d if removed_line.startswith("- "))]
    removed = [line[2:] for line in d if line.startswith("- ") and not any(added_line[2:] == line[2:] for added_line in d if added_line.startswith("+ "))]
    unified_diff = "\n".join(difflib.unified_diff(lines1, lines2, lineterm=""))

    def word_diff(line1, line2):
        return "".join(difflib.Differ().compare(line1.split(), line2.split()))

    changed_lines = []
    for i, line1 in enumerate(lines1):
        if i < len(lines2) and line1 != lines2[i]:
            changed_lines.append({
                "change_number": len(changed_lines) + 1,
                "original": {"content": line1},
                "modified": {"content": lines2[i], "diff": word_diff(line1, lines2[i])}
            })
        elif i >= len(lines2) and line1 not in removed:
            pass # Handled as removed

    for j, line2 in enumerate(lines2):
        if j >= len(lines1) and line2 not in added:
            pass # Handled as added
    return {
        "added": [line for line in added if line.strip()],
        "removed": [line for line in removed if line.strip()],
        "changed_lines": changed_lines,
        "unified_diff": unified_diff,
    }