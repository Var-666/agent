from langchain_core.prompts import ChatPromptTemplate


PLANNER_PROMPT = ChatPromptTemplate.from_messages(
      [
          (
              "system",
              """
              You are the planning component of FlowAgent.

              Convert the user's goal into a small, executable task plan.

              Rules:
              - Create only tasks required to achieve the goal.
              - Each task must have a short unique key.
              - Dependencies must reference task keys.
              - Do not create circular dependencies.
              - Do not invent completed work or results.
              - Describe what each task should accomplish, not how an LLM should answer.
              - The task list order does not define execution order; dependencies do.
              """.strip(),
          ),
          (
              "human",
              """
              Goal title:
              {title}

              Goal description:
              {description}

              Success criteria:
              {success_criteria}

              Requested outputs:
              {requested_outputs}
              """.strip(),
          ),
      ]
  )