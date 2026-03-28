import re
import time
import os


def _text_to_html_body(text):
    paragraphs = []
    current_list = []

    def flush_list():
        if current_list:
            items = "".join(f"<li>{item}</li>" for item in current_list)
            paragraphs.append(f"<ul>{items}</ul>")
            current_list.clear()

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped:
            flush_list()
            continue

        # Bullet points
        if stripped.startswith(("* ", "- ", "• ")):
            content = stripped[2:].strip()
            content = _format_inline(content)
            current_list.append(content)
            continue

        flush_list()

        # Headings (## or ###)
        if stripped.startswith("### "):
            paragraphs.append(f"<h3>{_format_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            paragraphs.append(f"<h2>{_format_inline(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            paragraphs.append(f"<h2>{_format_inline(stripped[2:])}</h2>")
        else:
            paragraphs.append(f"<p>{_format_inline(stripped)}</p>")

    flush_list()
    return "\n".join(paragraphs)


def _format_inline(text):
    # Bold (**text**)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic (*text*)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Clickable URLs
    text = re.sub(
        r'(https?://[^\s<>"`]+)',
        r'<a href="\1" target="_blank">\1</a>',
        text
    )
    return text


def _build_search_params_html(search_params):
    rows = "".join(
        f"<tr><td>{key}</td><td>{value}</td></tr>"
        for key, value in search_params.items()
    )
    return f"""
    <section class="search-params">
        <h2>Search Parameters</h2>
        <table>
            <tbody>{rows}</tbody>
        </table>
    </section>"""


def generate_html_report(ai_response_text, output_path, search_params=None):
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    body_html = _text_to_html_body(ai_response_text)
    params_html = _build_search_params_html(search_params) if search_params else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recommended Jobs</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 960px;
            margin: 40px auto;
            padding: 0 24px;
            color: #1a1a1a;
            background: #f9f9f9;
        }}
        header {{
            background: #0a66c2;
            color: white;
            padding: 24px 32px;
            border-radius: 8px;
            margin-bottom: 32px;
        }}
        header h1 {{
            margin: 0 0 4px 0;
            font-size: 1.6rem;
        }}
        header p {{
            margin: 0;
            opacity: 0.85;
            font-size: 0.9rem;
        }}
        .search-params {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px 24px;
            margin-bottom: 32px;
        }}
        .search-params h2 {{
            margin-top: 0;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        td {{
            padding: 8px 12px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 0.95rem;
        }}
        td:first-child {{
            font-weight: 600;
            color: #555;
            width: 220px;
        }}
        h2 {{
            color: #0a66c2;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 6px;
            margin-top: 36px;
        }}
        h3 {{
            color: #333;
            margin-top: 24px;
        }}
        p {{
            line-height: 1.7;
            margin: 8px 0;
        }}
        ul {{
            padding-left: 20px;
            margin: 8px 0;
        }}
        li {{
            line-height: 1.7;
            margin: 4px 0;
        }}
        a {{
            color: #0a66c2;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        strong {{
            color: #111;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Recommended Jobs</h1>
        <p>Generated on {current_time}</p>
    </header>
    {params_html}
    <main>
        {body_html}
    </main>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML report saved to {output_path}")


def extract_latest_recommendations(conversations_path):
    """Parse conversations.txt and return the last AI Response entry."""
    with open(conversations_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split on the separator used by write_to_text_file
    entries = content.split("*****************************************************")

    # Walk backwards to find the last AI Response block
    for entry in reversed(entries):
        if "AI Response:" in entry:
            # Strip the prefix and leading whitespace/timestamp line
            response_text = re.split(r'AI Response:\s*\n', entry, maxsplit=1)[-1].strip()
            return response_text

    return None


if __name__ == "__main__":
    import configparser

    conversations_path = "../data/conversations/conversations.txt"
    results_dir = "../data/results/"

    config = configparser.ConfigParser()
    config.read('../config.ini')
    search_params = {
        "Keywords": config['JOB_PARAMETERS']['keywords'],
        "Location": config['JOB_PARAMETERS']['location_name'],
        "Distance (miles)": config['JOB_PARAMETERS']['distance'],
        "Companies": config['JOB_PARAMETERS']['companies_literal'],
        "Years of Experience": config['USER_PARAMETERS']['years_of_experience'],
        "Education": f"{config['USER_PARAMETERS']['education_level']} in {config['USER_PARAMETERS']['education_field']}",
        "Minimum Salary": f"${int(config['USER_PARAMETERS']['minimum_salary']):,}",
    }

    response_text = extract_latest_recommendations(conversations_path)
    if not response_text:
        print("No AI responses found in conversations.txt")
    else:
        report_filename = time.strftime("%Y-%m-%d") + "_recommended_jobs.html"
        output_path = os.path.join(results_dir, report_filename)
        generate_html_report(response_text, output_path, search_params)
