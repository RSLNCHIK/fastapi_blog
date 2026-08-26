from fastapi import FastAPI, Request, HTTPException, status, Depends
# fastapi ist ein modernes web framework fuer Python, das auf standard python type hints basiert. Es ist schnell, einfach zu berechnen und zu implementieren. FastAPI ist ideal fuer die Erstellung von APIs und Webanwendungen.
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from .schemas import PostCreate, PostResponse, UserCreate, UserResponse

from typing import Annotated

from . import models
from .database import Base, engine, get_db


from sqlalchemy.orm import Session
from sqlalchemy import select

Base.metadata.create_all(bind=engine)



app = FastAPI()
# app ist eine Instanz der FastAPI-Klasse, die die Hauptanwendung darstellt. Sie wird verwendet, um Routen, Middleware und andere Funktionen zu definieren.
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
# was beduetet mout?
# Die Methode `app.mount()` wird verwendet, um eine bestimmte URL-Pfadpräfix (in diesem Fall "/static") mit einem bestimmten Verzeichnis auf dem Server zu verknüpfen (in diesem Fall das Verzeichnis "static"). Dies bedeutet, dass alle Anfragen, die mit "/static" beginnen, an die Dateien im "static"-Verzeichnis weitergeleitet werden. Zum Beispiel würde eine Anfrage an "/static/style.css" die Datei "style.css" aus dem "static"-Verzeichnis zurückgeben.
# und Static Files ist eine Klasse, die es ermöglicht, statische Dateien (wie CSS, JavaScript, Bilder usw.) aus einem bestimmten Verzeichnis zu servieren. In diesem Fall wird das Verzeichnis "static" verwendet, um statische Dateien bereitzustellen.
# und name ist ein optionaler Parameter, der einen Namen für die gemountete Anwendung angibt. In diesem Fall wird der Name "static" verwendet, um die gemountete Anwendung zu identifizieren.
templates = Jinja2Templates(directory="templates")


# @app.get("/", response_class=HTMLResponse, include_in_schema=False)
# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
# def home():
#     return {"message": "Hello, World!"}

# was ist @app.get("/") ist ein Dekorator, der eine Route für die HTTP GET-Methode definiert. In diesem Fall wird die Funktion home() aufgerufen, wenn ein GET-Request an die Wurzel-URL ("/") der Anwendung gesendet wird. Der Dekorator verbindet die URL mit der entsprechenden Funktion, sodass FastAPI weiß, welche Funktion ausgeführt werden soll, wenn diese Route aufgerufen wird.
# @app.get("/", include_in_schema=False, name="home")
# @app.get("/posts", include_in_schema=False, name="posts")
# name ist ein optionaler Parameter, der einen Namen für die Route angibt. In diesem Fall wird der Name "home" für die Wurzel-URL ("/") und "posts" für die URL "/posts" verwendet. Diese Namen können später verwendet werden, um auf die Routen zu verweisen, z.B. in Templates oder bei der Generierung von URLs.
# def home():
#     return f"<h1>FastAPI Blog</h1><p>Welcome to my FastAPI blog, actually {posts[0]["title"]}!</p>"

# def home(request: Request):
#     return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )


# @app.get("/posts/{post_id}", include_in_schema=False)
# def post_page(request: Request, post_id: int):
#     for post in posts:
#         if post["id"] == post_id:
#             title = post["title"][:50]
#             return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found:(")

@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")



@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    # Implementation for creating a new user
    result = db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    result = db.execute(select(models.User).where(models.User.email == user.email))

    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/user/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    # was ist scalars()? scalars() ist eine Methode, die auf einem SQLAlchemy Result-Objekt aufgerufen wird. Sie gibt eine Liste der ersten Spalte jeder Zeile im Ergebnis zurück. In diesem Fall wird sie verwendet, um das erste Ergebnis der Abfrage zu erhalten, das dem Benutzer mit der angegebenen user_id entspricht.

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


## user_posts_page
@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )
# was ist templates.TemplateResponse? templates.TemplateResponse ist eine Methode, die eine HTML-Vorlage rendert und eine HTTP-Antwort zurückgibt. Sie wird verwendet, um dynamische Inhalte in HTML-Seiten einzufügen. In diesem Fall wird die Vorlage "user_posts.html" gerendert und die Variablen "posts", "user" und "title" werden an die Vorlage übergeben, damit sie im HTML angezeigt werden können.

# @app.get("/api/posts", response_model=list[PostResponse])
# def get_posts():
#     return posts


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts

# @app.get("/api/post/{post_id}", response_model=PostResponse)
# def get_post(post_id: int):
#     for post in posts:
#         if post["id"] == post_id:
#             return post
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found:(")

@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

# Das ist fuer posts, wenn posts nicht in der Datenbank ist, dann wird eine leere Liste zurueckgegeben.
# @app.post(
#     "/api/posts",
#     response_model=PostResponse,
#     status_code=status.HTTP_201_CREATED,
# )

# def create_post(post: PostCreate):
#     new_id = max(p["id"] for p in posts) + 1 if posts else 1
#     new_post = {
#         "id": new_id,
#         "author": post.author,
#         "title": post.title,
#         "content": post.content,
#         "date_posted": "Juli 24, 2026",
#     }
#     posts.append(new_post)
#     return new_post



@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post



@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

# ist ein Modul eine Klasse oder Objekt? Ein Modul ist eine Datei, die Python-Code enthält. Es kann Funktionen, Klassen und Variablen enthalten, die in anderen Python-Dateien importiert und verwendet werden können. In diesem Fall ist `status` ein Modul in FastAPI, das HTTP-Statuscodes definiert.
# was ist status? status ist eine Klasse oder Objekt? status ist ein Modul in FastAPI, das HTTP-Statuscodes definiert. Es enthaelt Konstanten, die den verschiedenen HTTP-Statuscodes entsprechen, wie z.B. `status.HTTP_404_NOT_FOUND` für den Statuscode 404 (Not Found). Diese Konstanten können verwendet werden, um den Statuscode in HTTP-Antworten anzugeben, anstatt die numerischen Werte direkt zu verwenden.

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            # was wird hier gemacht? status_code=exception.status_code gibt den HTTP-Statuscode der Ausnahme zurück, die aufgetreten ist. exception.status_code ist eine Eigenschaft der StarletteHTTPException-Klasse, die den Statuscode der Ausnahme enthält. Dieser Statuscode wird in der JSON-Antwort zurückgegeben, um dem Client mitzuteilen, welcher Fehler aufgetreten ist.
            content={"detail": message},
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
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

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