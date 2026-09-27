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
        title="研究 LangChain 的最新更新",
        description=(
            "研究过去 7 天 LangChain 的重要更新，"
            "核实官方来源，"
            "并生成一份 Markdown 报告。"
        ),
        success_criteria=[
            "重要的主张应有官方来源支持。",
            "该报告应侧重于过去7天内的更新情况。",
        ],
        requested_outputs=[
            "Markdown report",
        ],
    )

    plan = planner.plan(goal)

    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
