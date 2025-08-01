# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LSP (Longevity Score Points) System - A health data-based scoring system that analyzes iOS HealthKit data to calculate longevity scores and incentivize healthy behaviors.

**Tech Stack**: Python 3.11+, PostgreSQL 14+, FastAPI, Pydantic

## Common Development Commands

### Running the Application
```bash
# Start the FastAPI server (port 8000)
python start_server.py

# Or using the main module directly
python -m src.main
```

### Testing
```bash
# Test database connection
python scripts/test_db_connection.py

# Test API endpoints
python scripts/test_api_endpoints.py

# Test score calculation
python scripts/test_score_calculation.py

# Quick API test
./quick_test.sh

# Test all APIs
python test_all_apis.py
```

### Database Operations
```bash
# Initialize database tables
python scripts/init_database.py

# Import HealthKit CSV data
python scripts/import_csv_to_db.py

# Add user_id support (migration)
python scripts/add_user_id_migration.py

# Add score expiration fields
python scripts/add_score_expiration_fields.py
```

### Docker Operations
```bash
# Build Docker image
./build.sh

# Deploy with docker-compose
docker-compose up -d

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## High-Level Architecture

### Core Components

1. **Score Engine** (`src/core/score_engine.py`)
   - Central orchestrator for score calculations
   - Integrates dimension calculators (Sleep, Exercise, Diet, Mental)
   - Handles user tier levels and chain reactions
   - Auto-saves scores to database

2. **Dimension Calculators** (`src/core/calculators/`)
   - Base class: `DimensionCalculator` - provides common interfaces
   - Each dimension (Sleep, Exercise, Diet, Mental) has specific calculation logic
   - Implements tier multipliers and chain punishment checks

3. **API Layer** (`src/api/`)
   - `health_data_api.py`: Health data retrieval endpoints
   - `score_api.py`: Score calculation and retrieval endpoints
   - `auth_api.py`: JWT-based authentication (optional)
   - Auth middleware supports both authenticated and anonymous modes

4. **Database Layer** (`src/db/`)
   - PostgreSQL connection pool pattern
   - Configuration through environment variables
   - Key tables: `health_metric`, `user_scores`, `users`

### Key Design Patterns

1. **Service Layer Pattern**
   - `HealthDataService`: Aggregates raw health metrics into daily summaries
   - `ScorePersistenceService`: Handles score storage with expiration logic

2. **Configuration Management**
   - Environment variables via `.env` file
   - Pydantic settings for type-safe configuration
   - Global config in `src/db/configs/global_config.py`

3. **Error Handling**
   - Consistent error responses with proper HTTP status codes
   - Database connection errors return 500
   - Comprehensive logging via custom logger

### Data Flow

1. **Health Data Import**
   - CSV → `import_csv_to_db.py` → `health_metric` table
   - Each record has: type, value, unit, start_date, end_date, user_id

2. **Score Calculation**
   - API request → ScoreEngine → Dimension Calculators
   - Fetches health data → Calculates scores → Saves to `user_scores`
   - Scores expire after 6 months

3. **Authentication Flow (Optional)**
   - Login → JWT token generation
   - Protected endpoints check Bearer token
   - Can be disabled via `AUTH_ENABLED=false`

## Important Implementation Details

- **User IDs**: All data is now multi-user aware with UUID user_ids
- **Score Expiration**: Scores older than 6 months are marked expired
- **Tier Levels**: Bronze, Silver, Gold, Platinum, Diamond, Ambassador
- **Chain Reactions**: 7-day history checked for punishment conditions
- **Idempotent Calculations**: Same input always produces same output

## API Documentation

- Swagger UI: http://localhost:8000/lsp/docs
- ReDoc: http://localhost:8000/lsp/redoc
- OpenAPI JSON: http://localhost:8000/lsp/openapi.json

## Current Implementation Status

**Implemented**: 4/8 dimensions (Sleep, Exercise, Diet, Mental)
**Pending**: Environment, Social, Cognitive, Prevention dimensions