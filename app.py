from flask import Flask, render_template, request
from reboot.workspace import inspect_project

from dotenv import load_dotenv
from reboot.agent import create_restart_plan

from reboot.arxiv_search import search_papers

load_dotenv()

app = Flask(__name__)
    
    
@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    plan = None
    error = None
    project_path = ""
    papers = []
    paper_query = ""

    if request.method == "POST":
        action = request.form.get("action", "inspect")

        if action == "search_papers":
            paper_query = request.form.get("paper_query", "").strip()

            try:
                papers = search_papers(paper_query)
            except (ValueError, RuntimeError) as exc:
                error = str(exc)

        else:
            project_path = request.form.get("project_path", "").strip()

            if not project_path:
                error = "Please enter a project folder path."
            else:
                try:
                    report = inspect_project(project_path)
                except Exception as exc:
                    app.logger.exception("Project inspection failed")
                    error = f"Project inspection failed: {exc}"
                else:
                    try:
                        plan = create_restart_plan(report)
                    except Exception as exc:
                        app.logger.exception("AI restart plan failed")
                        error = (
                            "The project was inspected successfully, "
                            f"but the AI plan failed: {type(exc).__name__}: {exc}"
                        )

    return render_template(
        "index.html",
        report=report,
        error=error,
        project_path=project_path,
        plan=plan,
        papers=papers,
        paper_query=paper_query,
    )



if __name__ == "__main__":
    app.run(debug=False)