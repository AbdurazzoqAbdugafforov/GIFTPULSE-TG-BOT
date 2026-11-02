#!/usr/bin/env python
"""GiftPulse 1-Command Universal Launcher.

Usage:
  python run.py            # Starts EVERYTHING (API + Telegram Bot + Data Ingestion)
  python run.py bot        # Starts Telegram Bot only
  python run.py api        # Starts FastAPI Mini App server only
  python run.py worker     # Starts background data ingestion worker only
"""
import sys
from app.main import main

if __name__ == "__main__":
    main()
