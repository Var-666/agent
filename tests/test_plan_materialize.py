from flow_agent.domain import TaskStatus
from flow_agent.planning.materialize import materialize_tasks
from flow_agent.planning.schema import ExecutionPlan, PlanTask


def test_materialize_plan_tasks():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Research and write",
        tasks=[
            PlanTask(
                key="search",
                title="Search",
                description="Search official sources",
            ),
            PlanTask(
                key="write",
                title="Write",
                description="Write report",
                dependencies=["search"],
            ),
        ],
    )

    tasks = materialize_tasks(plan)

    assert len(tasks) == 2

    search_task = tasks[0]
    write_task = tasks[1]

    assert search_task.title == "Search"
    assert write_task.title == "Write"

    assert search_task.status == TaskStatus.PENDING
    assert write_task.status == TaskStatus.PENDING

    assert write_task.dependencies == (
        search_task.id,
    )
    
def test_materialize_topologically_orders_tasks():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Research and write",
        tasks=[
            PlanTask(
                key="write",
                title="Write",
                description="Write report",
                dependencies=["search"],
            ),
            PlanTask(
                key="search",
                title="Search",
                description="Search sources",
            ),
        ],
    )

    tasks = materialize_tasks(plan)

    search_task = tasks[0]
    write_task = tasks[1]

    assert search_task.title == "Search"
    assert write_task.title == "Write"

    assert write_task.dependencies == (
        search_task.id,
    )
    
def test_materialized_task_uses_domain_id():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Search",
        tasks=[
            PlanTask(
                key="search",
                title="Search",
                description="Search sources",
            ),
        ],
    )

    task = materialize_tasks(plan)[0]

    assert task.id != "search"