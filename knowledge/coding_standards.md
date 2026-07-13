# Python FastAPI Backend Coding Standards

This document defines the architectural and coding standards for building scalable, maintainable, and robust microservices using FastAPI.

---

## 1. Architectural Pattern: Layered Bounded Contexts

The application must be split into top-level packages representing **Bounded Contexts** (e.g., `vouchers`, `users`).

Each context acts as an independent module. Cross-context communication must happen exclusively through public service interfaces, never by querying another context's database tables directly.

```
src/
    ├── app.py                  # FastAPI application initialization
    ├── config.py               # Global configuration and environment variables
    ├── database.py             # Global DB engine and session setup
    ├── vouchers/               # Bounded Context: Vouchers
    │   ├── init.py         # Explicit exports
    │   ├── routes.py           # FastAPI endpoints/routers
    │   ├── services.py         # Public API surface / Business logic
    │   ├── repositories.py     # Context-private persistence layer
    │   ├── models.py           # Database ORM models
    │   └── schemas.py          # Pydantic validation schemas
    └── users/                  # Bounded Context: Users
        ├── init.py
        ├── routes.py
        ├── services.py
        └── ...
```

---

## 2. Layer Responsibilities

### 2.1 Route Layer (`routes.py`)

- Contains only FastAPI path operations (`@router.get`, `@router.post`).
- Responsible for HTTP parsing, status codes, and request validation via Pydantic.
- Must inject the context service layer using FastAPI `Depends`.
- Contains zero business logic or direct database queries.

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db_session
from src.vouchers.schemas import VoucherCreate, VoucherResponse
from src.vouchers.services import VoucherService

router = APIRouter(prefix="/vouchers", tags=["Vouchers"])

async def get_voucher_service(db: AsyncSession = Depends(get_db_session)) -> VoucherService:
    return VoucherService(db)

@router.post("/", response_model=VoucherResponse, status_code=status.HTTP_201_CREATED)
async def create_new_voucher(
    payload: VoucherCreate,
    service: VoucherService = Depends(get_voucher_service)
):
    return await service.create_voucher(payload)
```

### 2.2 Service Layer (`services.py`)

- Acts as the public API surface for the bounded context.
- Orchestrates business rules, data transformations, and domain validations.
- Coordinates calls to the context-private persistence layer.
- Accepts and returns Pydantic models or domain objects, never raw DB models.

```python
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.vouchers.repositories import VoucherRepository
from src.vouchers.schemas import VoucherCreate, VoucherResponse

class VoucherService:
    def __init__(self, db: AsyncSession):
        self.repository = VoucherRepository(db)

    async def create_voucher(self, data: VoucherCreate) -> VoucherResponse:
        # Business validation logic
        existing = await self.repository.get_by_code(data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voucher code already exists"
            )

        db_voucher = await self.repository.create(data)
        return VoucherResponse.model_validate(db_voucher)
```

### 2.3 Persistence Layer (`repositories.py`)

- Strictly context-private. Other contexts cannot import this file.
- Abstract all SQL queries, SQLAlchemy operations, or external storage mechanisms.
- Returns SQLAlchemy ORM models or entities to the service layer.

```python
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.vouchers.models import VoucherDBModel
from src.vouchers.schemas import VoucherCreate

class VoucherRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, code: str) -> Optional[VoucherDBModel]:
        result = await self.db.execute(
            select(VoucherDBModel).where(VoucherDBModel.code == code)
        )
        return result.scalars().first()

    async def create(self, data: VoucherCreate) -> VoucherDBModel:
        db_item = VoucherDBModel(**data.model_dump())
        self.db.add(db_item)
        await self.db.commit()
        await self.db.refresh(db_item)
        return db_item
```

---

## 3. General Implementation Rules

- **Asynchronous Execution:** Use async/await definitions for all route handlers, service methods, and repository calls (`async def`).
- **Type Hinting:** Enforce strict type hinting on all function signatures, variables, and return values.
- **Pydantic v2 Standards:** Use `.model_dump()` instead of `.dict()`, and `.model_validate()` instead of `.from_orm()`.
- **Dependency Injection:** Utilize FastAPI's `Depends` for passing configuration, database sessions, and cross-context services.
