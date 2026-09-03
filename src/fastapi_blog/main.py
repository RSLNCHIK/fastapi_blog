from fastapi import FastAPI, Request, HTTPException, status, Depends
# fastapi ist ein modernes web framework fuer Python, das auf standard python type hints basiert. Es ist schnell, einfach zu berechnen und zu implementieren. FastAPI ist ideal fuer die Erstellung von APIs und Webanwendungen.
from contextlib import asynccontextmanager

from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
# from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from typing import Annotated

from . import models
from .database import Base, engine, get_db


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from .routers import users, posts


# Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Create the database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Schutdown the database engine
    await engine.dispose()
    # Drop the database tables (optional, for testing purposes)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)



app = FastAPI(lifespan=lifespan)
# app ist eine Instanz der FastAPI-Klasse, die die Hauptanwendung darstellt. Sie wird verwendet, um Routen, Middleware und andere Funktionen zu definieren.
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
# was beduetet mount?
# Die Methode `app.mount()` wird verwendet, um eine bestimmte URL-Pfadpräfix (in diesem Fall "/static") mit einem bestimmten Verzeichnis auf dem Server zu verknüpfen (in diesem Fall das Verzeichnis "static"). Dies bedeutet, dass alle Anfragen, die mit "/static" beginnen, an die Dateien im "static"-Verzeichnis weitergeleitet werden. Zum Beispiel würde eine Anfrage an "/static/style.css" die Datei "style.css" aus dem "static"-Verzeichnis zurückgeben.
# und Static Files ist eine Klasse, die es ermöglicht, statische Dateien (wie CSS, JavaScript, Bilder usw.) aus einem bestimmten Verzeichnis zu servieren. In diesem Fall wird das Verzeichnis "static" verwendet, um statische Dateien bereitzustellen.
# und name ist ein optionaler Parameter, der einen Namen für die gemountete Anwendung angibt. In diesem Fall wird der Name "static" verwendet, um die gemountete Anwendung zu identifizieren.
templates = Jinja2Templates(directory="templates")


app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


## user_posts_page
@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id),
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )

# get post page
@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id),
    )
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    if request.url.path.startswith("/api"):
        # return JSONResponse(
        #     status_code=exception.status_code,
        #     # was wird hier gemacht? status_code=exception.status_code gibt den HTTP-Statuscode der Ausnahme zurück, die aufgetreten ist. exception.status_code ist eine Eigenschaft der StarletteHTTPException-Klasse, die den Statuscode der Ausnahme enthält. Dieser Statuscode wird in der JSON-Antwort zurückgegeben, um dem Client mitzuteilen, welcher Fehler aufgetreten ist.
        #     content={"detail": message},
        # )
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )
# warum werden hier zwei status_code verwendet? Der erste status_code wird hier verwendet, um den HTTP-Statuscode der Ausnahme zurückzugeben, die aufgetreten ist. Der zweite status_code wird verwendet, um den HTTP-Statuscode der Antwort festzulegen, die an den Client zurückgegeben wird. In diesem Fall sind beide Statuscodes gleich, da die Antwort den gleichen Statuscode wie die Ausnahme haben sollte.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        # return JSONResponse(
        #     status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        #     content={"detail": exception.errors()},
        # )
        return await request_validation_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )