import os
from mangum import Mangum
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.routers.v1 import media_companies, media_teachers
from src.exceptions import media_except


STAGE = os.environ.get('STAGE')
root_path = '/' if not STAGE else f'/{STAGE}'
app = FastAPI(title='ForeignTeacher: Media Service', root_path=root_path)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BusinessException(Exception):
    def __init__(self, term: str):
        self.term = term

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=418,
        content={
            'code': 1,
            'msg': f'Oops! {exc.term} is a wrong phrase. Guess again?'
        }
    )


media_except.include_app(app)


router_v1 = APIRouter(prefix='/api/v1')
router_v1.include_router(media_teachers.router)
router_v1.include_router(media_companies.router)


app.include_router(router_v1)


@app.get('/search/{term}')
async def info(term: str):
    if term != 'yolo':
        raise BusinessException(term=term)
    return {'mention': 'You only live once'}


# Mangum Handler, this is so important
handler = Mangum(app)
