.PHONY: install scrape scrape_search_results jupyter backend frontend

install:
	@echo "📦 Installing Python dependencies with uv..."
	@uv sync
	@echo ""
	@echo "🎭 Installing Playwright browsers..."
	@uv run playwright install chromium
	@echo ""
	@echo "✅ Installation complete!"
	@echo ""
	@echo "Usage:"
	@echo "  make scrape               # Scrape listings"
	@echo "  make scrape_search_results  # Scrape search pages"
	@echo "  make jupyter              # Open Jupyter for data processing"

jupyter:
	@echo "📊 Starting Jupyter notebook..."
	@echo ""
	@echo "💡 Open 'househunter_workflow.ipynb' to process and analyze data"
	@echo ""
	@uv run jupyter notebook

scrape:
	@echo "🕷️  Starting manual scraper..."
	@echo "📋 Checking Chrome status..."
	@if curl -s http://localhost:9222/json/version >/dev/null 2>&1; then \
		echo "✅ Chrome already running with remote debugging"; \
	else \
		echo "🌐 Launching Chrome with remote debugging..."; \
		bash start_chrome.sh; \
		sleep 2; \
	fi
	@echo ""
	@echo "💾 Scraped data will be saved to: data/scraped/YYYY_MM_DD/"
	@echo ""
	@uv run python -m src.backend.manual_scraper

scrape_search_results:
	@echo "🔍 Starting search results scraper..."
	@echo "📋 Checking Chrome status..."
	@if curl -s http://localhost:9222/json/version >/dev/null 2>&1; then \
		echo "✅ Chrome already running with remote debugging"; \
	else \
		echo "🌐 Launching Chrome with remote debugging..."; \
		bash start_chrome.sh; \
		sleep 2; \
	fi
	@echo ""
	@echo "💾 Scraped data will be saved to: data/scraped/YYYY_MM_DD/search_results/"
	@echo ""
	@uv run python -m src.backend.manual_scraper_search

backend:
	uv run uvicorn src.backend.api.main:app --reload --port 8000

frontend:
	cd src/frontend && npm run dev
