---
name: testing
description: Technical blueprint and verification checklist for automated tests across the frontend React app (RTL/Vitest/MSW) and backend Python services (pytest/Testcontainers). Use whenever writing tests, or before committing code that needs test coverage.
metadata:
  version: "1.0"
---

Use these standards to maintain consistent, reliable, and deterministic test suites.

## Frontend Integration Tests (React)

Our frontend testing strategy focuses on user-centric integration testing. We avoid testing implementation details and instead verify that the application behaves correctly from the user's perspective.

### Core Stack

- **React Testing Library (RTL):** For rendering components and querying the DOM like a real user.
- **Vitest:** As the test runner and assertion library.
- **Mock Service Worker (MSW):** For mocking network-level HTTP requests.

### Key Practices

- **Query by Accessibility:** Always prefer `screen.getByRole` or `screen.findByRole` to ensure your HTML remains accessible.
  - If in doubt, follow the [official priority](https://testing-library.com/docs/queries/about/#priority) outlined in the Testing Library documentation.
- **User Events:** Use `@testing-library/user-event` instead of `fireEvent` to simulate realistic browser interactions.
- **Network Mocking:** Intercept API requests at the network layer using MSW. Never mock internal data-fetching hooks directly.

### Frontend Example (`src/components/UserProfile.test.tsx`)

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { beforeAll, afterEach, afterAll, expect, test } from 'vitest';
import { UserProfile } from './UserProfile';

// 1. Define MSW handlers for network isolation
const handlers = [
  http.get('/api/user', () => {
    return HttpResponse.json({ name: 'Alex Smith', email: 'alex@example.com' });
  }),
  http.post('/api/user/update', async ({ request }) => {
    const body = await request.json() as { name: string };
    return HttpResponse.json({ name: body.name, email: 'alex@example.com' });
  })
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// 2. Integration test suite
test('displays user profile and handles name update updates successfully', async () => {
  const user = userEvent.setup();
  render(<UserProfile />);

  // Verify initial data load via MSW
  const nameInput = await screen.findByRole('textbox', { name: /name/i });
  expect(nameInput).toHaveValue('Alex Smith');

  // Simulate user editing the form
  await user.clear(nameInput);
  await user.type(nameInput, 'Alex Jones');

  // Submit and verify updated state
  const saveButton = screen.getByRole('button', { name: /save/i });
  await user.click(saveButton);

  const successMessage = await screen.findByText(/profile updated successfully/i);
  expect(successMessage).toBeInTheDocument();
  expect(nameInput).toHaveValue('Alex Jones');
});
```

## Backend Integration Tests (Python & FastAPI)

Our backend integration testing strategy uses actual, ephemeral infrastructure to execute tests against a real database environment rather than using mock objects.

### Core Stack

- **pytest:** The primary test runner and fixture framework.
- **FastAPI TestClient:** For executing HTTP requests against the application routers.
- **Testcontainers (Postgres):** For automatically spinning up and tearing down a real Dockerised PostgreSQL database instance during the test run.
- **SQLAlchemy / Alembic:** For database connectivity and executing migrations.

### Key Practices

- **Database Isolation:** Run each test file or session inside an isolated database instance managed by Testcontainers.
- **Transaction Rollbacks:** Wrap each test in a database transaction that rolls back automatically upon completion to ensure a clean state for subsequent tests.
- **Async-Safe Fixtures:** Use appropriate async scopes (`pytest_asyncio`) if your FastAPI codebase relies on asynchronous database drivers.

### Backend Setup (`tests/conftest.py`)

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.main import app
from app.database import Base, get_db

@pytest.fixture(scope="session")
def postgres_container():
    """Spins up a real Postgres database in a Docker container for the test session."""
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Creates a SQLAlchemy engine connected to the Testcontainer instance."""
    engine = create_engine(postgres_container.get_connection_url())
    # Generate schema tables. If using migrations, run Alembic here instead.
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provides a transactional session that rolls back after each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Returns a FastAPI TestClient with the database dependency overridden."""
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### Backend Example (`tests/test_items.py`)

```python
from fastapi import status

def test_create_and_read_item(client):
    # 1. Arrange payload
    payload = {"name": "Widget", "description": "An automated testing utility"}

    # 2. Act: Create item
    create_response = client.post("/items/", json=payload)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_data = create_response.json()
    assert created_data["name"] == payload["name"]
    item_id = created_data["id"]

    # 3. Act: Read item back to confirm database persistence
    read_response = client.get(f"/items/{item_id}")
    assert read_response.status_code == status.HTTP_200_OK
    assert read_response.json()["description"] == payload["description"]
```

## Agent Verification Checklist

When creating or editing code, ensure your work complies with the following guidelines before committing:

1. **No `msw` Direct Imports in Components:** Keep your network mocks strictly inside your `*.test.*` files.
2. **No Hardcoded DB Credentials:** Always use `postgres_container.get_connection_url()` dynamically to fetch the connection string.
3. **Clean Up Mocks:** Confirm `server.resetHandlers()` is called after each test block to prevent test contamination.
4. **No Local State Leftovers:** Confirm that all database entries generated by backend tests are rolled back or truncated.
