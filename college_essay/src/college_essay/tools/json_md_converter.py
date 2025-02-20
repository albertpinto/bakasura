import json
from crewai_tools import tool

@tool
def json_to_markdown(json_file: str, output_md: str) -> str:
    """
    Converts a JSON file to a Markdown file.

    Args:
        json_file (str): Path to the input JSON file.
        output_md (str): Path to save the output Markdown file.

    Returns:
        str: Confirmation message with the output file path.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        md_content = "# Converted JSON to Markdown\n\n"

        def parse_json(data, indent=0):
            """Recursively parses JSON data into Markdown format."""
            md = ""
            for key, value in data.items():
                prefix = "#" * (indent + 2)  # Dynamic heading levels
                if isinstance(value, dict):
                    md += f"\n{prefix} {key}\n"
                    md += parse_json(value, indent + 1)
                elif isinstance(value, list):
                    md += f"\n{prefix} {key}\n"
                    for item in value:
                        if isinstance(item, dict):
                            md += parse_json(item, indent + 1)
                        else:
                            md += f"- {item}\n"
                else:
                    md += f"**{key}:** {value}\n\n"
            return md

        md_content += parse_json(data)

        # Write to Markdown file
        with open(output_md, "w", encoding="utf-8") as md_file:
            md_file.write(md_content)

        return f"✅ JSON converted to Markdown successfully: {output_md}"

    except Exception as e:
        return f"❌ Error converting JSON to Markdown: {str(e)}"
