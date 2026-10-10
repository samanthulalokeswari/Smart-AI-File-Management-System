
import os
import pandas as pd
import streamlit as st

from scan import scan_workspace
from organize import organize_files
from duplicate import find_duplicates, calculate_storage_savings
from report import create_category_report, get_workspace_summary
from ai_assistant import analyze_workspace
from crew_ai import run_file_management_crew
from utils import format_size


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Smart AI File Management System",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# SESSION STATE
# ==================================================

defaults = {
    "files": [],
    "folders": 0,
    "total_size": 0,
    "workspace_path": "",
    "scan_completed": False,
    "scan_stale": False,
    "organization_results": None,
    "duplicate_groups": {},
    "duplicate_scan_completed": False,
    "gemini_response": None,
    "crew_response": None,
    "report_data": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def get_category_counts(files):
    counts = {}

    for item in files:
        category = item.get("Category", "Others")
        counts[category] = counts.get(category, 0) + 1

    return counts


def calculate_workspace_size(files):
    total = 0

    for item in files:
        size = item.get("Size (Bytes)", item.get("size_bytes"))

        try:
            if size is not None:
                total += int(size)
            else:
                path = item.get("Path", item.get("path", ""))
                if path and os.path.isfile(path):
                    total += os.path.getsize(path)
        except (OSError, TypeError, ValueError):
            continue

    return total


def count_workspace_folders(folder):
    count = 0

    for _, directories, _ in os.walk(folder):
        count += len(directories)

    return count


def display_result(result):
    if isinstance(result, pd.DataFrame):
        st.dataframe(result, hide_index=True, width="stretch")
    elif isinstance(result, (dict, list)):
        st.json(result)
    else:
        st.write(result)


def local_recommendations(files, folders, total_size,
                          category_counts, reason):
    lines = [
        "### File Management Recommendations",
        "",
        f"**Status:** {reason}",
        "",
        "#### Workspace Summary",
        f"- Total files: {len(files):,}",
        f"- Total folders: {folders:,}",
        f"- Total storage: {format_size(total_size)}",
        "",
        "#### Recommendations"
    ]

    if category_counts:
        largest = max(category_counts, key=category_counts.get)
        lines.append(
            f"- The largest category by file count is {largest} "
            f"({category_counts[largest]} files)."
        )

    lines.extend([
        "- Keep files in clearly named category folders.",
        "- Review identical files before deleting any copies.",
        "- Archive files you no longer need regularly.",
        "- Back up important documents."
    ])

    return "\n".join(lines)


# ==================================================
# WORKSPACE SCANNER
# ==================================================

def run_scan(folder):
    folder = (folder or "").strip()

    if not folder:
        st.error("Please enter a workspace folder path.")
        return

    if not os.path.isdir(folder):
        st.error(f"Folder not found: {folder}")
        return

    try:
        with st.spinner("Scanning workspace..."):
            result = scan_workspace(folder)

            if isinstance(result, tuple):
                files = result[0]
            elif isinstance(result, dict):
                files = result.get("files", [])
            else:
                files = result

            if not isinstance(files, list):
                st.error("The scanner did not return a list of files.")
                return

            total_size = calculate_workspace_size(files)
            folders = count_workspace_folders(folder)

        st.session_state.files = files
        st.session_state.folders = folders
        st.session_state.total_size = total_size
        st.session_state.workspace_path = folder
        st.session_state.scan_completed = True
        st.session_state.scan_stale = False
        st.session_state.organization_results = None
        st.session_state.duplicate_groups = {}
        st.session_state.duplicate_scan_completed = False
        st.session_state.gemini_response = None
        st.session_state.crew_response = None
        st.session_state.report_data = None

        st.success(f"Scan completed! {len(files):,} files found.")

    except Exception as error:
        st.error(f"Unable to scan workspace: {error}")


# ==================================================
# FILE ORGANIZATION
# ==================================================

def run_organization():
    files = st.session_state.files
    folder = st.session_state.workspace_path

    if not files:
        st.warning("Please scan your workspace first.")
        return

    if st.session_state.scan_stale:
        st.warning("Rescan the workspace before organizing again.")
        return

    try:
        with st.spinner("Organizing files..."):
            results = organize_files(files, folder)

        st.session_state.organization_results = results
        st.session_state.scan_stale = True
        st.session_state.duplicate_groups = {}
        st.session_state.duplicate_scan_completed = False
        st.session_state.report_data = None

        st.success("Organization process finished.")
        st.warning(
            "Some files may have moved. Scan the workspace again "
            "to refresh file paths."
        )
        display_result(results)

    except Exception as error:
        st.error(f"Organization failed: {error}")


# ==================================================
# DUPLICATE DETECTION
# ==================================================

def run_duplicate_detection():
    files = st.session_state.files

    if not files:
        st.warning("Please scan your workspace first.")
        return

    if st.session_state.scan_stale:
        st.warning("Rescan the workspace after organizing files.")
        return

    try:
        with st.spinner("Checking file contents for duplicates..."):
            groups = find_duplicates(files)

        st.session_state.duplicate_groups = groups
        st.session_state.duplicate_scan_completed = True
        st.session_state.report_data = None

        st.success("Duplicate detection completed.")

    except Exception as error:
        st.error(f"Duplicate detection failed: {error}")


# ==================================================
# AI ANALYSIS
# ==================================================

def run_gemini_analysis():
    files = st.session_state.files

    if not files:
        st.warning("Please scan your workspace first.")
        return

    try:
        with st.spinner("Gemini is analyzing your workspace..."):
            response, error = analyze_workspace(
                files,
                st.session_state.folders,
                st.session_state.total_size,
                get_category_counts(files)
            )

        if error or not response:
            response = local_recommendations(
                files,
                st.session_state.folders,
                st.session_state.total_size,
                get_category_counts(files),
                "Gemini is unavailable or its request failed."
            )

        st.session_state.gemini_response = response

    except Exception as error:
        st.session_state.gemini_response = local_recommendations(
            files,
            st.session_state.folders,
            st.session_state.total_size,
            get_category_counts(files),
            f"Gemini analysis failed: {error}"
        )


def run_crew_analysis():
    files = st.session_state.files

    if not files:
        st.warning("Please scan your workspace first.")
        return

    if st.session_state.scan_stale:
        st.warning("Rescan the workspace before running CrewAI.")
        return

    try:
        with st.spinner("CrewAI agents are analyzing your workspace..."):
            response, error = run_file_management_crew(
                files,
                st.session_state.folders,
                st.session_state.total_size,
                get_category_counts(files),
                st.session_state.duplicate_groups
            )

        if error or not response:
            response = local_recommendations(
                files,
                st.session_state.folders,
                st.session_state.total_size,
                get_category_counts(files),
                "CrewAI or its AI service is unavailable."
            )

        st.session_state.crew_response = response

    except Exception as error:
        st.session_state.crew_response = local_recommendations(
            files,
            st.session_state.folders,
            st.session_state.total_size,
            get_category_counts(files),
            f"CrewAI workflow failed: {error}"
        )


# ==================================================
# REPORT GENERATION
# ==================================================

def run_report_generation():
    files = st.session_state.files

    if not files:
        st.warning("Please scan a workspace first.")
        return

    try:
        category_report = create_category_report(files)

        # Use exactly the duplicate groups shown in Duplicate Detection.
        groups = st.session_state.duplicate_groups or {}

        # Use the same savings function as Duplicate Detection.
        savings = calculate_storage_savings(groups)

        summary = {
            "Total Files": len(files),
            "Total Folders": st.session_state.folders,
            "Total Size": format_size(st.session_state.total_size),
            "Duplicate Groups": len(groups),
            "Duplicate Files": sum(len(group) for group in groups.values()),
            "Potential Storage Savings": format_size(savings)
        }

        st.session_state.report_data = {
            "summary": summary,
            "categories": category_report
        }

    except Exception as error:
        st.error(f"Unable to generate report: {error}")


# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("📁 Smart AI File Management System")
st.caption(
    "Intelligent file organization, duplicate detection, "
    "Gemini AI recommendations, CrewAI agents, and analytics."
)


# ==================================================
# LEFT SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("📁 Smart File Manager")
st.sidebar.caption("Workspace Control Center")
st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "🏠 Dashboard",
        "🔍 File Scanner",
        "📂 Organization",
        "♻️ Duplicate Detection",
        "🤖 AI Assistant",
        "📊 Reports"
    ],
    key="navigation_page"
)

st.sidebar.divider()
st.sidebar.subheader("Workspace Settings")

workspace_input = st.sidebar.text_input(
    "Workspace folder path",
    value=st.session_state.workspace_path,
    placeholder="C:/Users/HP/Documents",
    key="workspace_input"
)

if st.sidebar.button("🔎 Scan Workspace", type="primary",
                     use_container_width=True):
    run_scan(workspace_input)

if st.session_state.scan_completed:
    st.sidebar.success("Workspace scanned")
    st.sidebar.write(f"Files: {len(st.session_state.files):,}")
    st.sidebar.write(f"Storage: {format_size(st.session_state.total_size)}")

    if st.session_state.scan_stale:
        st.sidebar.warning("Rescan recommended after organization")


# ==================================================
# DASHBOARD
# ==================================================

if page == "🏠 Dashboard":
    st.subheader("Workspace Overview")

    if not st.session_state.scan_completed:
        st.info("Enter a folder path in the sidebar and click Scan Workspace.")
    else:
        files = st.session_state.files

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Files", f"{len(files):,}")
        col2.metric("Total Folders", f"{st.session_state.folders:,}")
        col3.metric("Total Storage", format_size(st.session_state.total_size))
        col4.metric("Duplicate Groups", len(st.session_state.duplicate_groups))

        counts = get_category_counts(files)

        if counts:
            st.subheader("Files by Category")
            df = pd.DataFrame(list(counts.items()),
                              columns=["Category", "Files"])
            st.bar_chart(df.set_index("Category"))

        st.subheader("Recent Scan Results")
        if files:
            st.dataframe(pd.DataFrame(files).head(100),
                         hide_index=True, width="stretch")
            st.caption("Showing up to 100 files.")


# ==================================================
# FILE SCANNER
# ==================================================

elif page == "🔍 File Scanner":
    st.subheader("File Scanner")

    if st.button("Scan Files", key="scanner_button"):
        run_scan(workspace_input)

    if st.session_state.scan_completed:
        files_df = pd.DataFrame(st.session_state.files)

        st.write(f"Files scanned: {len(files_df):,}")

        search_text = st.text_input(
            "Search by file name or path",
            key="file_search"
        )

        if search_text and not files_df.empty:
            matches = files_df.astype(str).apply(
                lambda col: col.str.contains(
                    search_text, case=False, na=False
                )
            ).any(axis=1)
            displayed_df = files_df[matches]
        else:
            displayed_df = files_df

        st.dataframe(displayed_df.head(2000),
                     hide_index=True, width="stretch")

        st.download_button(
            "Download Scanned File List (CSV)",
            data=displayed_df.to_csv(index=False).encode("utf-8"),
            file_name="scanned_files.csv",
            mime="text/csv"
        )
    else:
        st.info("Scan a workspace to view its files.")


# ==================================================
# ORGANIZATION
# ==================================================

elif page == "📂 Organization":
    st.subheader("Automated File Organization")

    st.warning(
        "This operation moves files into category folders. "
        "Choose your workspace carefully."
    )

    if st.session_state.files:
        counts = get_category_counts(st.session_state.files)

        st.markdown("### Organization Preview")
        preview = pd.DataFrame(list(counts.items()),
                               columns=["Category", "Files"])
        st.dataframe(preview, hide_index=True, width="stretch")

        confirm = st.checkbox(
            "I understand that this operation can move files."
        )

        if st.button("Organize Files", type="primary", disabled=not confirm):
            run_organization()

        if st.session_state.organization_results is not None:
            st.subheader("Organization Results")
            display_result(st.session_state.organization_results)
    else:
        st.info("Scan a workspace before organizing files.")


# ==================================================
# DUPLICATE DETECTION
# ==================================================

elif page == "♻️ Duplicate Detection":
    st.subheader("Duplicate File Detection")
    st.write(
        "Identify files with identical content and estimate potential savings."
    )

    if st.button("Find Duplicate Files", type="primary"):
        run_duplicate_detection()

    if st.session_state.duplicate_scan_completed:
        groups = st.session_state.duplicate_groups
        savings = calculate_storage_savings(groups)
        duplicate_count = sum(len(group) for group in groups.values())

        col1, col2, col3 = st.columns(3)
        col1.metric("Duplicate Groups", len(groups))
        col2.metric("Files in Duplicate Groups", duplicate_count)
        col3.metric("Potential Storage Savings", format_size(savings))

        if groups:
            st.subheader("Duplicate Groups")

            for index, (file_hash, group) in enumerate(groups.items(), 1):
                with st.expander(
                    f"Group {index} — {len(group)} matching files"
                ):
                    for item in group:
                        st.text(item.get("Path", item.get("Name", str(item))))
        else:
            st.success("No duplicate files were found.")

        st.caption(
            "Potential savings are estimates. Review duplicate files "
            "manually before deleting anything."
        )
    else:
        st.info("Run duplicate detection to view matching files.")


# ==================================================
# AI ASSISTANT
# ==================================================

elif page == "🤖 AI Assistant":
    st.subheader("AI Assistant")
    st.write(
        "Generate Gemini recommendations or run the CrewAI multi-agent workflow."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate Gemini Recommendations", type="primary"):
            run_gemini_analysis()

    with col2:
        if st.button("Run CrewAI Multi-Agent Workflow"):
            run_crew_analysis()

    st.divider()
    st.markdown("### Gemini API Results")

    if st.session_state.gemini_response:
        st.markdown(st.session_state.gemini_response)
    else:
        st.info("Gemini recommendations will appear here.")

    st.divider()
    st.markdown("### CrewAI Agent Report")

    if st.session_state.crew_response:
        st.markdown(st.session_state.crew_response)
    else:
        st.info("CrewAI results will appear here.")

    if not st.session_state.files:
        st.warning("Scan your workspace before running AI analysis.")


# ==================================================
# REPORTS AND ANALYTICS
# ==================================================

elif page == "📊 Reports":
    st.subheader("Workspace Reports and Analytics")

    if st.button("Generate Reports", type="primary"):
        run_report_generation()

    report_data = st.session_state.report_data

    if report_data:
        summary = report_data["summary"]
        category_report = report_data["categories"]

        st.markdown("### Workspace Summary")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Files", summary["Total Files"])
        col2.metric("Total Folders", summary["Total Folders"])
        col3.metric("Total Storage", summary["Total Size"])

        col4, col5, col6 = st.columns(3)
        col4.metric("Duplicate Groups", summary["Duplicate Groups"])
        col5.metric("Files in Duplicate Groups", summary["Duplicate Files"])
        col6.metric("Potential Storage Savings",
                    summary["Potential Storage Savings"])

        st.divider()
        st.markdown("### Category Report")

        if not category_report.empty:
            st.dataframe(
                category_report,
                hide_index=True,
                width="stretch"
            )

            if "Category" in category_report.columns and "Files" in category_report.columns:
                st.markdown("### Files by Category")
                chart_data = category_report[["Category", "Files"]].copy()
                st.bar_chart(chart_data.set_index("Category"))

            st.download_button(
                "Download Category Report (CSV)",
                data=category_report.to_csv(index=False).encode("utf-8"),
                file_name="workspace_category_report.csv",
                mime="text/csv"
            )
        else:
            st.info("No category data is available.")
    else:
        st.info("Click Generate Reports to view your workspace summary and category report.")
