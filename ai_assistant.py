
import os
from dotenv import load_dotenv
from google import genai
from utils import format_size

load_dotenv()


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def get_category_summary(files, category_counts=None):
    if category_counts is not None:
        if hasattr(category_counts, "to_string"):
            return category_counts.to_string(index=False)
        if isinstance(category_counts, dict):
            return "\n".join(
                f"{category}: {count}"
                for category, count in category_counts.items()
            )
        return str(category_counts)

    counts = {}

    for item in files:
        category = item.get("Category", "Others")
        counts[category] = counts.get(category, 0) + 1

    return "\n".join(
        f"{category}: {count}"
        for category, count in counts.items()
    ) or "No category data available"


def local_recommendations(files, folders, total_size, category_counts, reason):
    file_count = len(files)
    summary = get_category_summary(files, category_counts)

    try:
        readable_size = format_size(total_size)
    except (TypeError, ValueError):
        readable_size = str(total_size)

    categories = {}

    for item in files:
        category = item.get("Category", "Others")
        categories[category] = categories.get(category, 0) + 1

    lines = [
        "## Smart AI File Management Recommendations",
        "",
        "**Assistant mode:** Local fallback",
        "",
        "Gemini is temporarily unavailable, so these recommendations "
        "are generated from your scanned workspace data.",
        "",
        "### 1. Workspace Overview",
        f"- Total files scanned: {file_count}",
        f"- Total folders: {folders}",
        f"- Total storage size: {readable_size}",
        "",
        "### 2. File Category Analysis",
        summary,
        "",
        "### 3. Organization Recommendations",
    ]

    if file_count == 0:
        lines.append(
            "- No files were found. Check your workspace path and scan again."
        )
    else:
        largest_category = max(categories, key=categories.get)
        lines.append(
            f"- {largest_category} is your largest file category "
            f"by file count ({categories[largest_category]} files)."
        )
        lines.append(
            "- Keep files grouped into meaningful category folders."
        )
        lines.append(
            "- Review the Others category and manually classify "
            "important files where necessary."
        )

    lines.extend([
        "",
        "### 4. Duplicate File Management",
        "- Open Duplicate Detection to identify files with identical content.",
        "- Review duplicate groups before deleting anything.",
        "- Keep at least one verified copy of every important file.",
        "",
        "### 5. Storage Management",
        "- Review large files and remove only files you no longer need.",
        "- Back up important documents before performing cleanup.",
        "- Use the Reports page to review category storage usage.",
        "",
        "### 6. Workspace Maintenance",
        "- Scan your workspace regularly to keep file information up to date.",
        "- Avoid organizing system folders or files without checking their purpose.",
        "",
        "### Gemini API Status",
        reason,
    ])

    return "\n".join(lines)


def analyze_workspace(files, folders, total_size, category_counts):
    client = get_gemini_client()

    if client is None:
        return local_recommendations(
            files,
            folders,
            total_size,
            category_counts,
            "Gemini API key is missing or the client could not be initialized. "
            "Local recommendations are being displayed.",
        ), None

    prompt = f"""
You are an intelligent file management assistant.

Analyze this scanned workspace and give practical recommendations.

Total files: {len(files)}
Total folders: {folders}
Total size: {total_size}

File categories:
{get_category_summary(files, category_counts)}

Provide clear sections for:
1. Workspace analysis
2. File organization
3. Duplicate file management
4. Storage optimization
5. Workspace maintenance

Use simple language and recommendations supported by the supplied data.
Do not claim that files were deleted or moved unless that action occurred.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if response.text:
            return response.text, None

        raise ValueError("Gemini returned an empty response.")

    except Exception as error:
        error_text = str(error).lower()

        if (
            "429" in error_text
            or "resource_exhausted" in error_text
            or "quota" in error_text
        ):
            reason = (
                "Gemini request quota is exhausted. Wait for the quota to "
                "reset or check your Gemini API limits. No repeated request "
                "was made. Local recommendations are displayed instead."
            )
        else:
            reason = (
                "Gemini could not complete the request. Local "
                "recommendations are displayed instead."
            )

        return local_recommendations(
            files,
            folders,
            total_size,
            category_counts,
            reason,
        ), None
