#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
#  GRACE Prototype — Quick Start
#  Usage: ./start.sh
# ─────────────────────────────────────────────────────────────────────
set -e

BOLD="\033[1m"
BLUE="\033[34m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo ""
echo -e "${BLUE}${BOLD}🛡️  GRACE — Governance, Risk, Assurance & Compliance Engine${RESET}"
echo -e "${BLUE}    Prototype v1.0 · Brightstar Security Operations${RESET}"
echo ""

# Check ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo -e "${YELLOW}⚠  ANTHROPIC_API_KEY not set in environment.${RESET}"
  echo -e "   Enter your API key (from console.anthropic.com):"
  read -s -p "   > " ANTHROPIC_API_KEY
  echo ""
  export ANTHROPIC_API_KEY
fi
echo -e "${GREEN}✓  API key configured${RESET}"

# Check Docker
if ! command -v docker &> /dev/null; then
  echo -e "${RED}✗  Docker not found. Install Docker Desktop from https://docker.com${RESET}"
  exit 1
fi
echo -e "${GREEN}✓  Docker available${RESET}"

# Build and start
echo ""
echo -e "${BOLD}Building GRACE containers...${RESET}"
docker compose -f infrastructure/docker-compose.yml up --build -d

echo ""
echo -e "${BOLD}Waiting for services to start...${RESET}"
sleep 8

# Health check
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓  GRACE Backend online${RESET}"
else
  echo -e "${YELLOW}⚠  Backend still starting — check logs with: docker compose logs grace-backend${RESET}"
fi

echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${GREEN}${BOLD}  GRACE is running!${RESET}"
echo ""
echo -e "  🌐  Demo UI:   ${BOLD}http://localhost:8501${RESET}"
echo -e "  🔧  API docs:  ${BOLD}http://localhost:8000/docs${RESET}"
echo ""
echo -e "  Press Ctrl+C then run: ${BOLD}docker compose -f infrastructure/docker-compose.yml down${RESET} to stop"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

# Tail logs
docker compose -f infrastructure/docker-compose.yml logs -f
