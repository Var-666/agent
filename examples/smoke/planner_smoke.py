from dotenv import load_dotenv

from flow_agent.config import load_settings
from flow_agent.domain import Goal
from flow_agent.models import create_chat_model
from flow_agent.planning.planner import StructuredPlanner


def main() -> None:
    load_dotenv()

    settings = load_settings()

    model = create_chat_model(settings)

    planner = StructuredPlanner(model)

    goal = Goal(
        title="Research recent LangChain updates",
        description=(
            "Research important LangChain updates "
            "from the last 7 days, verify official sources, "
            "and produce a Markdown report."
        ),
        success_criteria=[
            "Important claims should be backed by official sources",
            "The report should focus on updates from the last 7 days",
        ],
        requested_outputs=[
            "Markdown report",
        ],
    )

    plan = planner.plan(goal)

    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()