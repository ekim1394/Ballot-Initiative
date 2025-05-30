import os
from enum import Enum
from io import BytesIO

from fastapi.responses import FileResponse
import pandas as pd
from fastapi import APIRouter, Request, Response, UploadFile
from app.voter_records.tables import Ballot, VoterRecord
from utils import logger

router = APIRouter(tags=["File Upload"])

if not os.path.exists("temp"):
    os.makedirs("temp")
    logger.info("Created temporary directory: temp")


class UploadFileTypes(str, Enum):
    voter_records = "voter_records"
    petition_signatures = "petition_signatures"


@router.delete("/clear")
def clear_all_files(request: Request):
    """
    Delete all files
    """
    request.state.voter_records_df = None
    if os.path.exists("temp/ballot.pdf"):
        os.remove("temp/ballot.pdf")
        logger.info("Deleted all files")
    else:
        logger.warning("No files to delete")
    return {"message": "All files deleted"}


@router.post("/upload/{filetype}")
async def upload_file(
    filetype: UploadFileTypes, file: UploadFile, response: Response, request: Request
):
    """Uploads file to the server and saves it to a temporary directory.

    Args:
        filetype (UploadFileTypes): can be voter_records or petition_signatures
    """
    logger.info(f"Received file: {file.filename} of type: {filetype}")

    # Validate file type extension
    match filetype:
        case UploadFileTypes.petition_signatures:
            if not file.filename.endswith(".pdf"):
                response.status_code = 400
                return {"error": "Invalid file type. Only pdf files are allowed."}
            contents = await file.read()
            instance = Ballot(name=file.filename, pdf_data=contents)
            await instance.save()
        case UploadFileTypes.voter_records:
            if not file.filename.endswith(".csv"):
                response.status_code = 400
                return {"error": "Invalid file type. Only .csv files are allowed."}
            contents = file.file.read()
            buffer = BytesIO(contents)
            df = pd.read_csv(buffer, dtype=str)

            required_columns = [
                "First_Name",
                "Last_Name",
                "Street_Number",
                "Street_Name",
                "Street_Type",
                "Street_Dir_Suffix",
            ]

            # Verify required columns
            if not all(col in df.columns for col in required_columns):
                response.status_code = 400
                return {"error": "Missing required columns in voter records file."}

            data = df.to_dict(orient="records")
            for row in data:
                instance = VoterRecord(**row)
                await instance.save()
            return {"message": f"{len(data)} voter records uploaded successfully"}
            

    return {"filename": file.filename}


@router.get("/upload/{filetype}")
def get_uploaded_file(filetype: UploadFileTypes, request: Request):
    """Returns the uploaded file.

    Args:
        filetype (UploadFileTypes): can be voter_records or petition_signatures
    """
    logger.info(f"Retrieving file of type: {filetype}")

    # Validate file type
    match filetype:
        case UploadFileTypes.petition_signatures:
            if not os.path.exists("temp/ballot.pdf"):
                return {"error": "No PDF file found for petition signatures"}
            return FileResponse("temp/ballot.pdf")
        case UploadFileTypes.voter_records:
            if request.app.state.voter_records_df is None:
                return {"error": "No voter records file found"}
            return request.app.state.voter_records_df.to_csv(index=False)
