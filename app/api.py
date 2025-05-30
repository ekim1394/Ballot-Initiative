import os

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.voter_records.tables import Ballot, VoterRecord
from fuzzy_match_helper import create_ocr_matched_df, create_select_voter_records
from ocr_helper import create_ocr_df
from routers import file
from settings.settings_repo import config
from utils import logger
from piccolo_api.fastapi.endpoints import FastAPIWrapper, FastAPIKwargs
from piccolo_api.crud.endpoints import PiccoloCRUD
from fastapi.routing import Mount
from piccolo_admin.endpoints import create_admin
from piccolo.engine import engine_finder
from contextlib import asynccontextmanager

app = FastAPI(root_path="/api")

origins = [
    "http://localhost",
    "http://localhost:5173",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

app.mount(
    path="/admin/",
    app=create_admin(
        tables=[Ballot, VoterRecord],
    ),
)
app.router.include_router(file.router, tags=["File Upload"])

FastAPIWrapper(
    root_url="/voter_record",
    fastapi_app=app,
    piccolo_crud=PiccoloCRUD(
        table=VoterRecord,
        read_only=False,
    ),
    fastapi_kwargs=FastAPIKwargs(all_routes={"tags": ["Voter Records"]}),
)

FastAPIWrapper(
    root_url="/ballot",
    fastapi_app=app,
    piccolo_crud=PiccoloCRUD(
        table=Ballot,
        read_only=False,
    ),
    fastapi_kwargs=FastAPIKwargs(all_routes={"tags": ["Ballot"]}),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    engine = engine_finder()
    await engine.start_connnection_pool()
    yield
    engine = engine_finder()
    await engine.close_connnection_pool()


@app.post("/ocr", tags=["OCR"])
def ocr(response: Response):
    """
    Triggers the OCR process on the uploaded petition signatures PDF file.
    """
    if not os.path.exists("temp/ballot.pdf"):
        logger.error("No PDF file found for petition signatures")
        response.status_code = 400
        return {"error": "No PDF file found for petition signatures"}
    if app.state.voter_records_df is None:
        logger.error("No voter records file found")
        response.status_code = 400
        return {"error": "No voter records file found"}
    logger.info("Starting OCR processing...")
    # Process files if in processing state
    logger.info("Converting PDF to images...")

    ocr_df = create_ocr_df(filedir="temp", filename="ballot.pdf")

    logger.info("Compiling Voter Record Data...")

    select_voter_records = create_select_voter_records(app.state.voter_records_df)

    logger.info("Matching petition signatures to voter records...")

    ocr_matched_df = create_ocr_matched_df(
        ocr_df, select_voter_records, threshold=config["BASE_THRESHOLD"]
    )
    response.headers["Content-Type"] = "application/json"
    return {"data": ocr_matched_df.to_dict(orient="records"), "stats": {}}
