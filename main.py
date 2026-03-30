from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app import models
from app import generator

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/css", StaticFiles(directory="css"), name="css")

def get_db():
    db = SessionLocal()
    
    try:
        yield db   
    finally:
        db.close()

def generate_unique_short_code(db, length=6):
    while(True):
        code = generator.generate_short_code()
        
        exists = db.query(models.ShortURL).filter(models.ShortURL.short_code == code).count()
        
        if not exists:
            return code

@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request, "result": ""}
        )

@app.post("/submit_form", response_class=HTMLResponse)
def handle_form(request: Request, input_url: str = Form(...), db: Session = Depends(get_db)):
    
    short_code = generate_unique_short_code(db)
    
    new_url = models.ShortURL(original_url=input_url, short_code=short_code)
    
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    
    result_text = f"Shortened URL: {request.base_url}{short_code}"
    
    return templates.TemplateResponse(
        request=request, name="index.html", context={"request": request, "result": result_text}
        )
    
@app.get("/{shortcode}")
def redirect_to_url(shortcode: str, db: Session = Depends(get_db)):
    url_record = db.query(models.ShortURL).filter(models.ShortURL.short_code == shortcode).first()
    
    if not url_record:
        raise HTTPException(status_code=404, detail="URL not found in db")
    
    return RedirectResponse(url=url_record.original_url)