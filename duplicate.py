import os
import hashlib


def calculate_hash(path):
    if not os.path.isfile(path):
        return None

    sha256 = hashlib.sha256()

    try:
        with open(path, "rb") as file:
            while True:
                chunk = file.read(1024 * 1024)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    except (PermissionError, OSError):
        return None


def find_duplicates(files):
    size_groups = {}

    for item in files:
        path = item["Path"]

        try:
            size = os.path.getsize(path)
        except (PermissionError, OSError):
            continue

        if size not in size_groups:
            size_groups[size] = []

        size_groups[size].append(item)

    duplicate_groups = {}

    for size, group in size_groups.items():

        if len(group) < 2:
            continue

        hash_groups = {}

        for item in group:

            file_hash = calculate_hash(
                item["Path"]
            )

            if file_hash is None:
                continue

            if file_hash not in hash_groups:
                hash_groups[file_hash] = []

            hash_groups[file_hash].append(item)

        for file_hash, matching_files in hash_groups.items():

            if len(matching_files) > 1:
                duplicate_groups[file_hash] = matching_files

    return duplicate_groups


def calculate_storage_savings(duplicate_groups):
    savings = 0

    for group in duplicate_groups.values():

        if len(group) > 1:

            try:
                file_size = os.path.getsize(
                    group[0]["Path"]
                )

                savings += (
                    file_size * (len(group) - 1)
                )

            except (PermissionError, OSError):
                continue

    return savings