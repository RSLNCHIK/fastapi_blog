from fastapi import FastAPI, Request, HTTPException, status
# fastapi ist ein modernes web framework fuer Python, das auf standard python type hints basiert. Es ist schnell, einfach zu berechnen und zu implementieren. FastAPI ist ideal fuer die Erstellung von APIs und Webanwendungen.
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse




app = FastAPI()
# app ist eine Instanz der FastAPI-Klasse, die die Hauptanwendung darstellt. Sie wird verwendet, um Routen, Middleware und andere Funktionen zu definieren.
app.mount("/static", StaticFiles(directory="static"), name="static")
# was beduetet mout?
# Die Methode `app.mount()` wird verwendet, um eine bestimmte URL-Pfadpräfix (in diesem Fall "/static") mit einem bestimmten Verzeichnis auf dem Server zu verknüpfen (in diesem Fall das Verzeichnis "static"). Dies bedeutet, dass alle Anfragen, die mit "/static" beginnen, an die Dateien im "static"-Verzeichnis weitergeleitet werden. Zum Beispiel würde eine Anfrage an "/static/style.css" die Datei "style.css" aus dem "static"-Verzeichnis zurückgeben.
# und Static Files ist eine Klasse, die es ermöglicht, statische Dateien (wie CSS, JavaScript, Bilder usw.) aus einem bestimmten Verzeichnis zu servieren. In diesem Fall wird das Verzeichnis "static" verwendet, um statische Dateien bereitzustellen.
# und name ist ein optionaler Parameter, der einen Namen für die gemountete Anwendung angibt. In diesem Fall wird der Name "static" verwendet, um die gemountete Anwendung zu identifizieren.
templates = Jinja2Templates(directory="templates")
posts: list[dict] = [
    {
        "id": 1,
        "author": "Ruslan Aliev",
        "title": "FastAPI, the first time",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "Juli 20, 2026",
    },
    {
        "id": 2,
        "author": "Jane Walker",
        "title": "Python ist Great for a Web Development",
        "content": "Python ist a great language for web development, and FastAPI makes it even better",
        "date_posted": "Juli 21, 2026",
    }
]

# @app.get("/", response_class=HTMLResponse, include_in_schema=False)
# @app.get("/posts", response_class=HTMLResponse, include_in_schema=False)
# def home():
#     return {"message": "Hello, World!"}

# was ist @app.get("/") ist ein Dekorator, der eine Route für die HTTP GET-Methode definiert. In diesem Fall wird die Funktion home() aufgerufen, wenn ein GET-Request an die Wurzel-URL ("/") der Anwendung gesendet wird. Der Dekorator verbindet die URL mit der entsprechenden Funktion, sodass FastAPI weiß, welche Funktion ausgeführt werden soll, wenn diese Route aufgerufen wird.
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
# name ist ein optionaler Parameter, der einen Namen für die Route angibt. In diesem Fall wird der Name "home" für die Wurzel-URL ("/") und "posts" für die URL "/posts" verwendet. Diese Namen können später verwendet werden, um auf die Routen zu verweisen, z.B. in Templates oder bei der Generierung von URLs.
# def home():
#     return f"<h1>FastAPI Blog</h1><p>Welcome to my FastAPI blog, actually {posts[0]["title"]}!</p>"

def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"})

@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request, post_id: int):
    for post in posts:
        if post["id"] == post_id:
            title = post["title"][:50]
            return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found:(")


@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts


@app.get("/api/post/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    for post in posts:
        if post["id"] == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found:(")

@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)

def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "Juli 24, 2026",
    }
    posts.append(new_post)
    return new_post

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