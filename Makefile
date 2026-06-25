# Install dependencies for both backend and frontend
install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

# Start development environment
dev:
	./scripts/dev.sh

# Build production-ready frontend
build:
	cd frontend && npm run build

# Run tests for backend and frontend
test:
	pytest backend/tests
	cd frontend && npm test

# Start Docker containers
docker-up:
	docker-compose up --build -d

# Stop Docker containers
docker-down:
	docker-compose down

# Clean up Docker containers, volumes, and images
clean:
	docker-compose down -v
	docker system prune -f