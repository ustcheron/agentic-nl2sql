import requests
from mcp.server.fastmcp import FastMCP  # 假设您已有这个基础库

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.abspath(os.path.join(current_dir, "../../.."))


if project_root not in sys.path:
    sys.path.append(project_root)

from utils import exec_sql

mcp = FastMCP("LocalServer")

@mcp.tool()
def sql_mcp(sql: str, db_id: str):
    return exec_sql(sql, db_id)


if __name__ == "__main__":
    print("\nStart MCP service:")
    mcp.run(transport='stdio')