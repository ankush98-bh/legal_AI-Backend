import re
import json
import html

def format_response(text):
    try:
        # Check if the entire response is a JSON object
        json_data = json.loads(text)
        return json.dumps(json_data)
    except json.JSONDecodeError:
        # Not a complete JSON object, continue with formatting
        pass
    
    # Create HTML version for rich formatting
    html_version = text
    
    # Process code blocks first (store and replace to protect them from other formatting)
    code_blocks = []
    
    def replace_code_block(match):
        language = match.group(1) or ""
        code = match.group(2)
        # Keep indentation intact by using <pre> tag
        formatted_code = f'<pre class="code-block {language}">{html.escape(code)}</pre>'
        code_blocks.append(formatted_code)
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    html_version = re.sub(r'```([a-zA-Z0-9]*)\n(.*?)\n```', replace_code_block, html_version, flags=re.DOTALL)
    
    # Format inline code
    inline_code_blocks = []
    
    def replace_inline_code(match):
        code = match.group(1)
        formatted_code = f'<code>{html.escape(code)}</code>'
        inline_code_blocks.append(formatted_code)
        return f"__INLINE_CODE_{len(inline_code_blocks)-1}__"
    
    html_version = re.sub(r'`([^`]+)`', replace_inline_code, html_version)
    
    # Format bold text
    html_version = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html_version)
    
    # Format italic text
    html_version = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html_version)
    
    # Format headers
    for i in range(6, 0, -1):
        pattern = r'^' + r'#' * i + r' (.+)$'
        html_version = re.sub(pattern, f'<h{i}>\\1</h{i}>', html_version, flags=re.MULTILINE)
    
    # Format bullet points
    html_version = re.sub(r'^(\s*)-\s+(.+)$', r'\1<li>\2</li>', html_version, flags=re.MULTILINE)
    
    # Format numbered lists
    html_version = re.sub(r'^(\s*)(\d+)\.\s+(.+)$', r'\1<li value="\2">\3</li>', html_version, flags=re.MULTILINE)
    
    # Replace code block placeholders with the actual HTML
    for i, block in enumerate(code_blocks):
        html_version = html_version.replace(f"__CODE_BLOCK_{i}__", block)
    
    # Replace inline code placeholders
    for i, code in enumerate(inline_code_blocks):
        html_version = html_version.replace(f"__INLINE_CODE_{i}__", code)
    
    # Ensure line breaks and paragraphs are properly separated
    html_version = re.sub(r'\n\n+', '</p><p>', html_version)
    html_version = re.sub(r'\n', '<br>', html_version)
    html_version = f"<p>{html_version}</p>"
    
    return html_version #return only the html string.