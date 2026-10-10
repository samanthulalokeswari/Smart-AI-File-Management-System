def format_size(size):
    if size < 1024:
        return f"{size} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.2f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.2f} MB"

    return f"{size / (1024 ** 3):.2f} GB"


def get_category(extension):
    extension = extension.lower()

    categories = {
        "Documents": [
            ".pdf", ".doc", ".docx", ".txt", ".rtf",
            ".xls", ".xlsx", ".csv", ".ppt", ".pptx"
        ],
        "Images": [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp",
            ".webp", ".svg", ".tiff"
        ],
        "Videos": [
            ".mp4", ".mkv", ".avi", ".mov", ".wmv",
            ".flv", ".webm"
        ],
        "Audio": [
            ".mp3", ".wav", ".aac", ".flac", ".ogg",
            ".m4a", ".wma"
        ],
        "Archives": [
            ".zip", ".rar", ".7z", ".tar", ".gz",
            ".bz2"
        ],
        "Applications": [
            ".exe", ".msi", ".apk"
        ],
        "Code": [
            ".py", ".java", ".c", ".cpp", ".js",
            ".html", ".css", ".sql", ".json", ".xml"
        ]
    }

    for category, extensions in categories.items():
        if extension in extensions:
            return category

    return "Others"