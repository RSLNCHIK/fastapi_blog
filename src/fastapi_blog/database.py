from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
# was macht die yield-Anweisung in der get_db Funktion? Die yield-Anweisung in der get_db-Funktion wird verwendet, um einen Generator zu erstellen. Ein Generator ist eine spezielle Art von Iterator, der Werte "on-the-fly" erzeugt und zurueck gibt, anstatt alle Werte auf einmal zu speichern. In diesem Fall wird die yield-Anweisung verwendet, um eine Datenbank-Session (db) zur Verfuegung zu stellen, die in den FastAPI-Endpunkten verwendet werden kann. Wenn die Funktion aufgerufen wird, wird die Session erstellt und an den Aufrufer zurueckgegeben. Nach der Verwendung der Session wird sie automatisch geschlossen, sobald der Generator beendet ist. 