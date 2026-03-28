import os
import glob

for path in glob.glob("docs/*.md"):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("---\n", 2)
    # The first split part is empty string before the first ---
    # The second part is the frontmatter content
    # The third part is the rest of the markdown
    if len(parts) >= 3 and "image:" not in parts[1]:
        parts[1] += "image: assets/social-banner.png\n"
        new_content = "---\n".join(parts)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
