import os
import asyncio
from mangum import Mangum
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.routers.v1 import media_links
from src.infra.resources.manager import resource_manager
from src.configs import exceptions


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

@app.on_event('startup')
async def startup_event():
    # init global connection pool
    await resource_manager.initial()
    asyncio.create_task(resource_manager.keeping_probe())


@app.on_event('shutdown')
async def shutdown_event():
    # close connection pool
    await resource_manager.close()


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


exceptions.include_app(app)

router_v1 = APIRouter(prefix='/media/api/v1')
router_v1.include_router(media_links.router)

app.include_router(router_v1)


@app.get('/search/{term}')
async def info(term: str):
    if term != 'yolo':
        raise BusinessException(term=term)
    return {'mention': 'You only live once'}


# Mangum Handler, this is so important
handler = Mangum(app)
