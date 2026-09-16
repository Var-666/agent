from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from tools.tool import Tool, ToolResult


class TimeArguments(BaseModel):
  timezone:str = Field(
    default="Asia/Shanghai",
    description="时区名称，例如 Asia/Shanghai、Asia/Tokyo、UTC"
  )


class TimeTool(Tool[TimeArguments]):

  def __init__(self):
    super().__init__(
      name="get_current_time",
      description="获取指定时区的当前时间",
      arguments_model=TimeArguments
    )

  def run(self,arguments:TimeArguments)->ToolResult:
    current_time = datetime.now(ZoneInfo(arguments.timezone))

    return current_time.strftime("%Y-%m-%d %H:%M:%S")
