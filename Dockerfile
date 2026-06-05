FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system -e .

ENV ODOO_MCP_TRANSPORT=stdio

CMD ["python", "-m", "mcp_server_odoo"]
