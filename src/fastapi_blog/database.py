# from sqlalchemy import create_engine
# from sqlalchemy.orm import DeclarativeBase, sessionmaker

# We use async engine and sessionmaker for asynchronous database opertaions
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase



SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

AsyncSessionLocal = async_sessionmaker(engine, 
                                  class_=AsyncSession,
                                  expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# def get_db():
#     with SessionLocal() as db:
#         yield db
# was macht die yield-Anweisung in der get_db Funktion? Die yield-Anweisung in der get_db-Funktion wird verwendet, um einen Generator zu erstellen. Ein Generator ist eine spezielle Art von Iterator, der Werte "on-the-fly" erzeugt und zurueck gibt, anstatt alle Werte auf einmal zu speichern. In diesem Fall wird die yield-Anweisung verwendet, um eine Datenbank-Session (db) zur Verfuegung zu stellen, die in den FastAPI-Endpunkten verwendet werden kann. Wenn die Funktion aufgerufen wird, wird die Session erstellt und an den Aufrufer zurueckgegeben. Nach der Verwendung der Session wird sie automatisch geschlossen, sobald der Generator beendet ist. 


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session