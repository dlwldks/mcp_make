from flood_report import generate_report, ReportRequest

def execute_tool(tool_name: str, input_data: dict):
    if tool_name == "flood_report":
        request = ReportRequest(**input_data)
        return generate_report(request)
    else:
        return {"error": f"Unknown tool: {tool_name}"}