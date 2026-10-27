"""Fresh selection after a bounded ray-cover fix and one new stress style.

The original selection and full SHA plan remain preserved. Final 830000-series
holdout seeds have not selected any policy. See PROTOCOL_V2.md before running.
"""
import workflow

workflow.PLAN_REVISION = 2
workflow.PLAN = workflow.HERE / "workflow-v2-plan.json"
workflow.LOCK = workflow.HERE / "selection-v2-lock.json"
workflow.REPORT = workflow.HERE / "FINAL_REPORT_V2.json"
workflow.NEW_TEAMS = ["experiments/league/ray_cover2/team.py",
                      "experiments/league/guardian/team.py",
                      "experiments/league/adaptive3/team.py"]
workflow.OPPONENTS = workflow.OPPONENTS + ["experiments/league/opponents/open_gap/team.py"]
workflow.SELECTION = [("league-selection-v2-custom", "custom", 822000, 822002),
                      ("league-selection-v2-default", "default", 822002, 822004)]
workflow.HOLDOUT = [("league-holdout-v2-default", "default", 830000, 830005),
                    ("league-holdout-v2-custom", "custom", 830005, 830010)]


if __name__ == "__main__":
    workflow.main()
