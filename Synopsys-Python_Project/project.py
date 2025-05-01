import re
import os
import argparse

class MarkdownConverter:
    def __init__(self, markdown_file: str):
        self.markdown_file = markdown_file
        self.html_output = ""
        self.lines = []
        self.in_code_block = False
        self.current_list_type = None
        self.list_buffer = []
        self.in_blockquote = False
        self.in_table = False
        self.table_header = True

    def load_file(self):
        with open(self.markdown_file, "r", encoding="utf-8") as file:
            self.lines = file.readlines()

    def convert(self):
        self.load_file()
        for line in self.lines:
            processed_line = self.process_line(line.rstrip())
            if processed_line:
                self.html_output += processed_line + "\n"
        self.close_list_if_open()
        self.close_blockquote_if_open()
        self.close_table_if_open()
        return self.wrap_html(self.html_output)

    def wrap_html(self, content: str) -> str:
        return (
            "<!DOCTYPE html>\n"
            "<html>\n<head>\n<meta charset='UTF-8'>\n<title>Markdown Output</title>\n"
            "<style>body { font-family: Arial; line-height: 1.6; padding: 20px; }</style>\n</head>\n<body>\n"
            + content + "\n</body>\n</html>"
        )

    def process_line(self, line: str) -> str:
        if self.in_code_block:
            if line.strip() == "```":
                self.in_code_block = False
                return "</code></pre>"
            else:
                return self.escape_html(line)
        elif line.strip() == "```":
            self.in_code_block = True
            return "<pre><code>"

        if not line.strip():
            return self.close_list_if_open() + self.close_blockquote_if_open() + self.close_table_if_open()

        # Horizontal rule
        if re.match(r"^(-{3,}|\*{3,})$", line):
            return "<hr>"

        # Blockquote
        if line.startswith(">"):
            return self.handle_blockquote(line[1:].strip())

        # Table
        if "|" in line:
            return self.handle_table(line)

        # Headings
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            self.close_table_if_open()
            hashes, content = heading_match.groups()
            level = len(hashes)
            content = self.parse_inline_styles(content)
            return f"<h{level}>{content}</h{level}>"

        # Lists
        unordered_match = re.match(r"^[-*+]\s+(.*)", line)
        ordered_match = re.match(r"^\d+\.\s+(.*)", line)

        if unordered_match:
            return self.handle_list("ul", unordered_match.group(1))

        if ordered_match:
            return self.handle_list("ol", ordered_match.group(1))

        self.close_list_if_open()
        self.close_blockquote_if_open()
        self.close_table_if_open()
        return f"<p>{self.parse_inline_styles(line)}</p>"

    def parse_inline_styles(self, text: str) -> str:
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\\1</strong>", text)
        text = re.sub(r"\*(.*?)\*", r"<em>\\1</em>", text)
        text = re.sub(r"`(.*?)`", r"<code>\\1</code>", text)
        text = re.sub(r"!\[(.*?)\]\((.*?)\)", r"<img alt='\\1' src='\\2'>", text)
        text = re.sub(r"\[(.*?)\]\((.*?)\)", r"<a href='\\2'>\\1</a>", text)
        return text

    def handle_list(self, list_type: str, item: str) -> str:
        html_item = f"<li>{self.parse_inline_styles(item)}</li>"

        if self.current_list_type == list_type:
            return html_item

        result = ""
        if self.current_list_type:
            result += self.close_list_if_open()

        self.current_list_type = list_type
        result += f"<{list_type}>\n{html_item}"
        return result

    def close_list_if_open(self) -> str:
        if self.current_list_type:
            closing_tag = f"</{self.current_list_type}>"
            self.current_list_type = None
            return closing_tag
        return ""

    def handle_blockquote(self, text: str) -> str:
        if not self.in_blockquote:
            self.in_blockquote = True
            return f"<blockquote>{self.parse_inline_styles(text)}"
        else:
            return self.parse_inline_styles(text)

    def close_blockquote_if_open(self) -> str:
        if self.in_blockquote:
            self.in_blockquote = False
            return "</blockquote>"
        return ""

    def handle_table(self, line: str) -> str:
        cells = [cell.strip() for cell in line.strip().split("|") if cell.strip()]
        if not cells:
            return ""

        html = ""
        if not self.in_table:
            self.in_table = True
            self.table_header = True
            html += "<table border='1' cellpadding='5' cellspacing='0'>\n"

        if self.table_header:
            html += "<tr>" + "".join([f"<th>{self.parse_inline_styles(cell)}</th>" for cell in cells]) + "</tr>"
            self.table_header = False
        else:
            html += "<tr>" + "".join([f"<td>{self.parse_inline_styles(cell)}</td>" for cell in cells]) + "</tr>"

        return html

    def close_table_if_open(self) -> str:
        if self.in_table:
            self.in_table = False
            return "</table>"
        return ""

    def escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def save_output(self, output_file: str):
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(self.html_output)

# CLI Execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Markdown file to HTML.")
    parser.add_argument("input", help="Markdown file to convert")
    parser.add_argument("output", help="Output HTML file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Markdown file '{args.input}' not found.")
        exit(1)

    converter = MarkdownConverter(args.input)
    html = converter.convert()
    converter.html_output = html
    converter.save_output(args.output)

    print(f"✅ HTML file generated: {args.output}")
