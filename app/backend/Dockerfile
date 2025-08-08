# Backend Dockerfile (FastAPI + MCP capable)
FROM node:20-bullseye-slim AS node-base
# Preinstall all MCP servers and Playwright to avoid npx fetching at runtime
# and ensure the CLIs are available in the final image.
RUN npm install -g \
    @azure/mcp@latest \
    @azure-devops/mcp@latest \
    github-mcp-custom \
    @playwright/mcp \
    @modelcontextprotocol/server-github \
    playwright

FROM python:3.11-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps + ICU (required by Azure MCP .NET host) + Azure CLI
RUN apt-get update && apt-get install -y \
    curl git ca-certificates gnupg \
    libicu-dev \
    # common fonts and utils used by headless browsers
    fonts-liberation \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxshmfence1 \
    libxkbcommon0 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash || true

# Copy Node executables from node-base
COPY --from=node-base /usr/local/bin/node /usr/local/bin/
COPY --from=node-base /usr/local/bin/npm /usr/local/bin/
COPY --from=node-base /usr/local/bin/npx /usr/local/bin/
COPY --from=node-base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Ensure node is on PATH for scripts using `#!/usr/bin/env node`
RUN ln -sf /usr/local/bin/node /usr/bin/node
# Copy globally installed MCP CLI shims into PATH
COPY --from=node-base /usr/local/bin/github-mcp-custom /usr/local/bin/github-mcp-custom
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"

# Pre-install Playwright browser deps and Chromium so @playwright/mcp can run
# Note: playwright CLI is available via global install in the node-base stage
RUN npx playwright install-deps chromium && \
    npx playwright install chromium

WORKDIR /app

# Install Python deps: backend-only (avoid root requirements conflicts)
COPY app/backend/requirements.txt ./backend-requirements.txt
RUN pip install --no-cache-dir -r backend-requirements.txt

# Copy code
COPY . ./

EXPOSE 8000
CMD ["uvicorn", "app.backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
