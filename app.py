from flask import Flask, render_template, request
from reboot.workspace import inspect_project

from dotenv import load_dotenv
from reboot.agent import create_restart_plan

load_dotenv()

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    error = None
    project_path = ""
    plan = None

    
    if request.method == "POST":
        project_path = request.form.get("project_path", "").strip()

        if not project_path:
            error = "Please enter a project folder path."
        else:
            try:
                report = inspect_project(project_path)
            except (ValueError, OSError, UnicodeError) as exc:
                error = f"Project inspection failed: {exc}"
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
        plan=plan,
        project_path=project_path,
    )


if __name__ == "__main__":
    app.run(debug=False)