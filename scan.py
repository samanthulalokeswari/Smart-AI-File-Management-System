import os
import pandas as pd
from utils import format_size, get_category


def scan_workspace(folder):
    files = []
    folders = 0
    total_size = 0

    for root, dirnames, filenames in os.walk(folder):

        folders += len(dirnames)

        for filename in filenames:

            path = os.path.join(
                root,
                filename
            )

            try:

                size = os.path.getsize(path)
                modified = os.path.getmtime(path)
                extension = os.path.splitext(
                    filename
                )[1].lower()

                files.append({
                    "Name": filename,
                    "Path": path,
                    "Extension": extension if extension else "No Extension",
                    "Category": get_category(extension),
                    "Size": format_size(size),
                    "Size (Bytes)": size,
                    "Modified": pd.to_datetime(
                        modified,
                        unit="s"
                    )
                })

                total_size += size

            except (PermissionError, OSError):

                continue

    return files, folders, total_size