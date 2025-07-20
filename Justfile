setup:
    @echo "🚀 Setting up Reactrine development environment..."
    @echo ""
    @echo "🎨 Installing frontend dependencies..."
    npm install --prefix frontend
    @echo ""
    @echo "🐍 Installing backend dependencies..."
    pip install -r backend/requirements.txt
    @echo ""
    @echo "🔧 Installing Python development tools..."
    pip install ruff black==25.1.0 isort mypy pip-audit pre-commit pytest-cov
    @echo ""
    @echo "🔗 Installing pre-commit hooks..."
    pre-commit install
    @echo ""
    @echo "🔐 Setting up secrets for development..."
    ./scripts/setup-secrets.sh
    @echo ""
    @echo "✅ Setup complete! Next steps:"
    @echo "   1. Update secrets in the secrets/ directory with your actual values"
    @echo "   2. Run 'just start' to start the development stack"
    @echo "   3. Run 'just logs' to view application logs"

start:
    @echo "Starting application stack locally..."
    docker compose up --build -d

stop:
    @echo "Stopping local stack..."
    docker compose down

restart:
    @echo "Restarting local stack..."
    docker compose down
    docker compose up --build -d
    just logs

logs:
    @echo "Tailing logs from running containers..."
    docker compose logs -f

healthcheck:
    @echo "Checking health of local stack..."
    curl -X 'GET' 'http://127.0.0.1:8000/api/v1/health'  -H 'accept: application/json'

lint:
    @echo "Running Python linter (ruff)..."
    ruff check backend
    @echo "Running Python type checker (mypy)..."
    mypy backend
    @echo "Running ESLint for JS/TS..."
    npm run lint --prefix frontend

format:
    @echo "Running Python formatter (black + isort)..."
    black backend
    isort backend
    @echo "Running Prettier for JS/TS..."
    npm run format --prefix frontend

test:
    @echo "Running all tests..."
    just test-be
    just test-fe

test-be:
    @echo "Running backend tests..."
    cd backend && ENVIRONMENT=test python -m pytest app/tests/ -v

test-fe:
    @echo "Running frontend tests..."
    cd frontend && npm run test -- --run

test-e2e:
    @echo "Running E2E tests..."
    # TODO: Add Cypress command
    @echo "Not yet implemented"

coverage:
    @echo "Running all tests with coverage..."
    just coverage-be
    just coverage-fe
    @echo ""
    @echo "📊 Coverage Summary:"
    @echo "Backend coverage: See backend/htmlcov/index.html"
    @echo "Frontend coverage: See frontend/coverage/index.html"

coverage-be:
    @echo "Running backend tests with coverage..."
    cd backend && ENVIRONMENT=test python -m pytest app/tests/ -v --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=60

coverage-fe:
    @echo "Running frontend tests with coverage..."
    cd frontend && npm run test:coverage -- --run

coverage-report:
    @echo "Generating combined coverage report..."
    just coverage-be
    just coverage-fe
    @echo ""
    @echo "📊 Coverage Reports Generated:"
    @echo "📁 Backend HTML Report: file://$(pwd)/backend/htmlcov/index.html"
    @echo "📁 Frontend HTML Report: file://$(pwd)/frontend/coverage/index.html"
    @echo ""
    @echo "💡 Tip: Open these HTML files in your browser to view detailed coverage reports"

coverage-quick:
    @echo "Running quick coverage check..."
    @echo "Backend coverage:"
    @cd backend && ENVIRONMENT=test python -m pytest app/tests/ -q --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=60
    @echo ""
    @echo "Frontend coverage:"
    @cd frontend && npm run test:coverage -- --run --reporter=basic

typecheck:
    @echo "Running type checking..."
    @echo "Checking backend types with mypy..."
    mypy backend
    @echo "Checking frontend types with tsc (excluding tests)..."
    cd frontend && npx tsc --project tsconfig.json --noEmit

build:
    @echo "Building for production..."
    @echo "Building frontend..."
    cd frontend && npm run build
    @echo "Building production Docker images..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml build

db-migrate:
    @echo "Generating new migration..."
    cd backend && alembic revision --autogenerate -m "Auto migration"

db-upgrade:
    @echo "Applying pending migrations..."
    cd backend && alembic upgrade head

db-seed:
    @echo "Seeding database..."
    # TODO: Add database seeding command
    @echo "Not yet implemented"

generate-pak-keys:
    @echo "Generating RSA keypair for Personal API Keys..."
    python backend/scripts/generate-pak-keypair.py

deploy-pi:
    @echo "🚀 Running simplified Raspberry Pi deployment script..."
    @echo "   • Uses multi-stage Docker build for API client generation"
    @echo "   • No temporary infrastructure needed"
    @./scripts/deploy-pi.sh


audit-deps:
    @echo "Auditing frontend dependencies..."
    npm audit --prefix frontend
    @echo "Auditing backend dependencies..."
    pip-audit

# Generate the frontend API client from the backend OpenAPI spec
api-client:
    cd frontend && npm run gen:api

pre-commit:
    @echo "Running pre-commit hooks on all files..."
    pre-commit run --all-files
cloc:
    @echo "Running cloc to count lines of code..."
    cloc . --exclude-dir=node_modules,.git,dist,build,coverage,__pycache__,.venv,env,tests,migrations,.mypy_cache --exclude-ext=json,md,txt

cloc-prod:
    @echo "Running cloc to count production lines of code (excluding test files)..."
    cloc . --exclude-dir=node_modules,.git,dist,build,coverage,__pycache__,.venv,env,tests,migrations,.mypy_cache,__tests__,test,e2e,integration,unit --exclude-ext=json,md,txt --match-f="^(?!.*\.test\.|.*\.spec\.|.*\.e2e\.|.*test_|.*_test\.)" --not-match-f="\.test\.|\.spec\.|\.e2e\.|test_|_test\.|conftest\.py|setup\.ts"

# Background Tasks Commands

worker:
    @echo "🔄 Starting Celery worker locally..."
    @echo "Make sure Redis is running (just start-redis or docker-compose up redis)"
    cd backend && celery -A app.worker.celery_app worker --loglevel=info --concurrency=2

start-redis:
    @echo "🔄 Starting Redis container..."
    docker compose up -d redis

stop-redis:
    @echo "🛑 Stopping Redis container..."
    docker compose stop redis

flower:
    @echo "🌸 Starting Flower monitoring..."
    @echo "Flower will be available at http://localhost:5555"
    docker compose --profile observability up -d flower

worker-status:
    @echo "📊 Checking Celery worker status..."
    cd backend && celery -A app.worker.celery_app inspect active

purge-tasks:
    @echo "🧹 Purging all tasks from queues..."
    @echo "This will remove all pending tasks. Continue? (Ctrl+C to cancel)"
    @read -p "Press Enter to continue..."
    cd backend && celery -A app.worker.celery_app purge -f

test-tasks:
    @echo "🧪 Running background task tests..."
    cd backend && ENVIRONMENT=test python -m pytest app/tests/test_*task* -v
