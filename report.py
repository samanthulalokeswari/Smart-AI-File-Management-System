
import pandas as pd

from utils import format_size
from duplicate import calculate_storage_savings


def create_category_report(files):
    category_counts = {}
    category_sizes = {}

    for item in files:
        category = item.get("Category", "Others")

        try:
            size = int(item.get("Size (Bytes)", 0) or 0)
        except (TypeError, ValueError):
            size = 0

        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )
        category_sizes[category] = (
            category_sizes.get(category, 0) + size
        )

    return pd.DataFrame({
        "Category": list(category_counts.keys()),
        "Files": list(category_counts.values()),
        "Total Size": [
            format_size(category_sizes[category])
            for category in category_counts
        ],
        "Size (Bytes)": [
            category_sizes[category]
            for category in category_counts
        ]
    })


def get_workspace_summary(
    files,
    folders,
    total_size,
    duplicate_groups
):
    duplicate_groups = duplicate_groups or {}

    duplicate_files = sum(
        len(group)
        for group in duplicate_groups.values()
    )

    duplicate_savings = calculate_storage_savings(
        duplicate_groups
    )

    return {
        "Total Files": len(files),
        "Total Folders": folders,
        "Total Size": format_size(total_size),
        "Duplicate Groups": len(duplicate_groups),
        "Duplicate Files": duplicate_files,
        "Potential Storage Savings": format_size(
            duplicate_savings
        )
    }


def get_category_counts(files):
    category_counts = {}

    for item in files:
        category = item.get("Category", "Others")
        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )

    return pd.DataFrame({
        "Category": list(category_counts.keys()),
        "Files": list(category_counts.values())
    })


def get_category_sizes(files):
    category_sizes = {}

    for item in files:
        category = item.get("Category", "Others")

        try:
            size = int(item.get("Size (Bytes)", 0) or 0)
        except (TypeError, ValueError):
            size = 0

        category_sizes[category] = (
            category_sizes.get(category, 0) + size
        )

    return pd.DataFrame({
        "Category": list(category_sizes.keys()),
        "Size (Bytes)": list(category_sizes.values()),
        "Size": [
            format_size(size)
            for size in category_sizes.values()
        ]
    })
