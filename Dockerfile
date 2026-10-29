FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml README.md ./
COPY mcp_server_odoo/ ./mcp_server_odoo/

RUN uv pip install --system .

ENV ODOO_MCP_TRANSPORT=stdio

CMD ["python", "-m", "mcp_server_odoo"]
