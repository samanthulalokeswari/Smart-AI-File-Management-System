
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()


def run_file_management_crew(
    files,
    folders,
    total_size,
    category_counts,
    duplicate_groups=None
):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None, "GEMINI_API_KEY is missing from your .env file."

    categories = {}

    for item in files:
        category = item.get("Category", "Others")
        categories[category] = categories.get(category, 0) + 1

    duplicate_groups = duplicate_groups or {}
    duplicate_file_count = sum(
        len(group) for group in duplicate_groups.values()
    )

    workspace_data = f"""
    Total files: {len(files)}
    Total folders: {folders}
    Total size in bytes: {total_size}
    Categories: {categories}
    Duplicate groups detected: {len(duplicate_groups)}
    Files in duplicate groups: {duplicate_file_count}
    """

    try:
        llm = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=api_key,
            temperature=0.2
        )

        file_analyst = Agent(
            role="File Analysis Specialist",
            goal="Analyze workspace statistics and identify useful patterns.",
            backstory=(
                "You analyze file metadata, categories, and storage usage "
                "to help users understand their workspace."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        organization_advisor = Agent(
            role="File Organization Specialist",
            goal="Recommend a clear and practical folder organization plan.",
            backstory=(
                "You specialize in organizing documents, images, videos, "
                "audio files, code, archives, and other files."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        duplicate_analyst = Agent(
            role="Duplicate Detection Specialist",
            goal="Interpret duplicate detection results and suggest safe cleanup.",
            backstory=(
                "You help users understand duplicate files and potential "
                "storage savings while protecting important data."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        report_writer = Agent(
            role="File Management Report Specialist",
            goal="Combine findings into a concise, actionable report.",
            backstory=(
                "You prepare clear workspace reports with findings, "
                "recommendations, and safe next steps."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False
        )

        analysis_task = Task(
            description=(
                "Analyze the following workspace data and summarize the "
                "main findings, category distribution, and storage usage.\n"
                f"{workspace_data}"
            ),
            expected_output=(
                "A concise analysis of workspace statistics and findings."
            ),
            agent=file_analyst
        )

        organization_task = Task(
            description=(
                "Using the workspace data and analysis, recommend practical "
                "file organization improvements. Do not claim that any files "
                "have already been moved.\n"
                f"{workspace_data}"
            ),
            expected_output=(
                "A practical organization plan based on the available data."
            ),
            agent=organization_advisor,
            context=[analysis_task]
        )

        duplicate_task = Task(
            description=(
                "Explain the duplicate detection results and recommend safe "
                "ways to review duplicates. Never recommend automatic deletion "
                "without user verification.\n"
                f"{workspace_data}"
            ),
            expected_output=(
                "Duplicate findings and safe storage cleanup recommendations."
            ),
            agent=duplicate_analyst,
            context=[analysis_task]
        )

        report_task = Task(
            description=(
                "Combine the workspace analysis, organization plan, and "
                "duplicate findings into a final report with clear headings."
            ),
            expected_output=(
                "A final report containing findings and actionable recommendations."
            ),
            agent=report_writer,
            context=[analysis_task, organization_task, duplicate_task]
        )

        crew = Crew(
            agents=[
                file_analyst,
                organization_advisor,
                duplicate_analyst,
                report_writer
            ],
            tasks=[
                analysis_task,
                organization_task,
                duplicate_task,
                report_task
            ],
            process=Process.sequential,
            verbose=False
        )

        result = crew.kickoff()
        return str(result), None

    except Exception as error:
        error_text = str(error).lower()

        if (
            "429" in error_text
            or "quota" in error_text
            or "resource_exhausted" in error_text
        ):
            return None, (
                "CrewAI could not complete its Gemini-powered analysis "
                "because the Gemini API quota is exhausted. Please use the "
                "local AI recommendations while the quota resets."
            )

        return None, (
            "CrewAI analysis could not be completed. Check the terminal "
            "for setup details. Error: " + str(error)
        )
