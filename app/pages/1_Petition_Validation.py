import streamlit as st
import pandas as pd
import os
import glob
from loguru import logger
import time
from dotenv import load_dotenv
import streamlit_shadcn_ui as ui
import json
import fitz  # PyMuPDF
from PIL import Image

from ocr_helper import create_ocr_df
from fuzzy_match_helper import create_select_voter_records, create_ocr_matched_df


# setting up logger for benchmarking, comment in to write logs to data/logs/benchmark_logs.log
logger.remove()
# logger.add("data/logs/benchmark_logs.log", rotation="10 MB", level="INFO")

# loading environmental variables
load_dotenv(".env", override=True)

# name of uploaded pdf file
UPLOADED_FILENAME = "ballot.pdf"

# name of repo
repo_name = "Ballot-Initiative"
REPODIR = os.getcwd().split(repo_name)[0] + repo_name

# load config
with open("config.json", "r") as f:
    config = json.load(f)


##
# DELETE TEMPORARY FILES
##


def wipe_all_temp_files():
    """Wipes all temporary files and resets session state"""
    try:
        # Clear temp directory
        temp_files = [
            file.path for file in os.scandir("./temp") if file.name != ".gitkeep"
        ]
        for file in temp_files:
            os.remove(file)

        # Reset session state for data and files
        if "voter_records_df" in st.session_state:
            del st.session_state.voter_records_df
        if "processed_results" in st.session_state:
            del st.session_state.processed_results
        if "signature_file" in st.session_state:
            del st.session_state.signature_file
        if "voter_records_file" in st.session_state:
            del st.session_state.voter_records_file

        # Instead of directly modifying file uploader states,
        # we'll use a flag to trigger a rerun
        st.session_state.clear_files = True

        return True
    except Exception as e:
        st.error(f"Error clearing files: {str(e)}")
        return False


##
# STREAMLIT APPLICATION
##

st.set_page_config(page_title="Petition Validation", page_icon="🗳️")

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #cce5ff;
        border: 1px solid #b8daff;
        color: #004085;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Application Header
st.header("Petition Validation")
st.caption("Automated signature verification for ballot initiatives")
st.markdown(
    "<hr style='height:3px;border:none;color:#0066cc;background-color:#0066cc;'/>",
    unsafe_allow_html=True,
)

start_time = None

# Add these session state initializations near the top with other session state setup
if "is_processing_complete" not in st.session_state:
    st.session_state.is_processing_complete = False
if "current_progress" not in st.session_state:
    st.session_state.current_progress = 0
if "progress_text" not in st.session_state:
    st.session_state.progress_text = ""


@st.cache_data
def load_voter_records(voter_records_file):
    """Cache and process voter records file"""
    df = pd.read_csv(voter_records_file, dtype=str)

    # Create necessary columns
    df["Full Name"] = df["First_Name"] + " " + df["Last_Name"]
    df["Full Address"] = (
        df["Street_Number"]
        + " "
        + df["Street_Name"]
        + " "
        + df["Street_Type"]
        + " "
        + df["Street_Dir_Suffix"]
    )
    return df


@st.cache_data
def load_signatures(signatures_file):
    """Cache and process signatures PDF file"""
    pdf_bytes = signatures_file.read()
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)

    # Save PDF to temp directory
    pdf_path = os.path.join("temp", UPLOADED_FILENAME)
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Convert first page for preview using PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    first_page = doc[0]
    pix = first_page.get_pixmap()
    preview_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    num_pages = len(doc)
    doc.close()

    return pdf_bytes, preview_image, num_pages


# Sidebar with improved styling
with st.sidebar:
    st.markdown("### 📝 Instructions")

    with st.expander("1️⃣ Upload Voter Records", expanded=False):
        st.markdown("""
        - CSV format required
        - Must include:
            - First_Name
            - Last_Name
            - Street_Number
            - Street_Name
            - Street_Type
            - Street_Dir_Suffix
        - *Example: Download a sample of fake voter records [here](https://github.com/Civic-Tech-Ballot-Inititiave/Ballot-Initiative/blob/main/sample_data/fake_voter_records.csv).*
        """)

    with st.expander("2️⃣ Upload Signatures", expanded=False):
        st.markdown("""
        - PDF format only
        - Clear, legible scans
        - One signature per line
        - *Example: Download a sample of fake signed petitions [here](https://github.com/Civic-Tech-Ballot-Inititiave/Ballot-Initiative/blob/main/sample_data/fake_signed_petitions_1-10.pdf).*
        """)

    with st.expander("3️⃣ Process & Review", expanded=False):
        st.markdown("""
        - Click 'Process Files'
        - Review matches
        - Download CSV results
        - *Note: Moving to the 'Home' page will restart processing.*
        """)

    with st.expander("4️⃣ Clear Files", expanded=False):
        st.markdown("""
        - Clear temporary files when done
        """)

# Initialize session state for data storage
if "voter_records_df" not in st.session_state:
    st.session_state.voter_records_df = None
if "processed_results" not in st.session_state:
    st.session_state.processed_results = None


# Add this near the top of your app, after session state initialization
if "clear_files" in st.session_state and st.session_state.clear_files:
    st.session_state.clear_files = False
    st.rerun()


# Main content area with file uploads
st.markdown("### Upload Files")
col1, col2 = st.columns(2, gap="large")

if "voter_records_file" not in st.session_state:
    st.session_state.voter_records_file = None

with col1:
    st.markdown("""
    #### 📄 Voter Records
    Upload your CSV file containing voter registration data.
    Required columns: `First_Name`, `Last_Name`, `Street_Number`, 
                             `Street_Name`, `Street_Type`, `Street_Dir_Suffix`
    """)

    voter_records = st.file_uploader(
        "Choose CSV file",
        type=["csv"],
        key="voter_records",
        help="Upload a CSV file containing voter registration data",
        on_change=lambda: setattr(
            st.session_state, "voter_records_file", st.session_state.voter_records
        ),
    )

    # Restore file from session state if available
    if voter_records is None and st.session_state.voter_records_file is not None:
        voter_records = st.session_state.voter_records_file

    # Process voter records when uploaded
    if voter_records is not None:
        try:
            df = load_voter_records(voter_records)

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
                st.error("Missing required columns in CSV file")
            else:
                st.session_state.voter_records_df = df
                st.success("✅ Voter records loaded successfully!")

                # Display preview
                with st.expander("Preview Voter Records"):
                    st.dataframe(df.head(), use_container_width=True)
                    st.caption(f"Total records: {len(df):,}")

        except Exception as e:
            st.error(f"Error loading voter records: {str(e)}")

# Initialize session state for file uploads
if "signature_file" not in st.session_state:
    st.session_state.signature_file = None

with col2:
    st.markdown("""
    #### ✍️ Petition Signatures
    Upload your PDF file containing petition pages with signatures. Each file will be cropped to focus on the section where the signatures are located. 
    Ensure these sections have the printed name and address of the voter. 
    """)

    signatures = st.file_uploader(
        "Choose PDF file",
        type=["pdf"],
        key="signatures",
        help="Upload a PDF containing scanned signature pages",
        on_change=lambda: setattr(
            st.session_state, "signature_file", st.session_state.signatures
        ),
    )

    # Restore file from session state if available
    if signatures is None and st.session_state.signature_file is not None:
        signatures = st.session_state.signature_file

    # Process PDF when uploaded
    if signatures is not None:
        try:
            pdf_bytes, preview_image, num_pages = load_signatures(signatures)
            st.success("✅ Petition signatures loaded successfully!")

            # Display preview
            with st.expander("Preview Petition Signatures"):
                st.markdown("**Preview of First Page:**")
                st.image(preview_image, width=300)
                st.caption(f"Total pages: {num_pages}")

        except Exception as e:
            st.error(f"Error processing ballot signatures: {str(e)}")

# Divider
st.markdown("---")

# Process Files Button
st.markdown("### Process Files")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.voter_records_df is None or signatures is None:
        st.warning("⚠️ Please upload both files to proceed")
    else:
        # Initialize cancel state if not exists
        if "processing_cancelled" not in st.session_state:
            st.session_state.processing_cancelled = False

        # Show either process or cancel button
        if not st.session_state.get("is_processing", False):
            process_button = st.button(
                "🚀 Process Files", type="primary", use_container_width=True
            )
            if process_button:
                st.session_state.is_processing = True
                st.rerun()
        else:
            if st.button(
                "⚠️ Cancel Processing",
                type="secondary",
                use_container_width=True,
                help="Note: Moving to the 'Home' page will restart processing.",
            ):
                st.caption("Processing cancelled by user")
                st.session_state.processing_cancelled = True
                st.session_state.is_processing = False
                st.session_state.is_processing_complete = False
                st.session_state.processing_cancelled = False
                st.session_state.current_progress = 0
                st.session_state.progress_text = ""
                st.rerun()

        # Process files if in processing state
        if (
            st.session_state.get("is_processing", False)
            and not st.session_state.is_processing_complete
        ):
            start_time = time.time()
            with st.spinner("Processing signatures for validation..."):
                try:
                    matching_bar = st.progress(
                        st.session_state.current_progress,
                        text=st.session_state.progress_text
                        or "Loading PDF of signed petitions...",
                    )

                    # Check for cancellation
                    if st.session_state.processing_cancelled:
                        st.warning("Processing cancelled by user")
                        st.session_state.is_processing = False
                        st.session_state.is_processing_complete = False
                        st.session_state.processing_cancelled = False
                        st.session_state.current_progress = 0
                        st.session_state.progress_text = ""
                        st.rerun()

                    # Update progress state as processing continues
                    st.session_state.current_progress = 0.0
                    st.session_state.progress_text = "Converting PDF to images..."
                    matching_bar.progress(
                        st.session_state.current_progress,
                        text=st.session_state.progress_text,
                    )

                    pdf_full_path = glob.glob(os.path.join("temp", UPLOADED_FILENAME))[
                        0
                    ]

                    if st.session_state.processing_cancelled:
                        raise InterruptedError("Processing cancelled by user")

                    st.session_state.current_progress = 0.3
                    matching_bar.progress(
                        st.session_state.current_progress,
                        text=st.session_state.progress_text,
                    )

                    ocr_df = create_ocr_df(
                        filedir="temp", filename=UPLOADED_FILENAME, st_bar=matching_bar
                    )

                    if st.session_state.processing_cancelled:
                        raise InterruptedError("Processing cancelled by user")

                    st.session_state.current_progress = 0.9
                    st.session_state.progress_text = "Compiling Voter Record Data"
                    matching_bar.progress(
                        st.session_state.current_progress,
                        text=st.session_state.progress_text,
                    )

                    select_voter_records = create_select_voter_records(
                        st.session_state.voter_records_df
                    )

                    if st.session_state.processing_cancelled:
                        raise InterruptedError("Processing cancelled by user")

                    st.session_state.current_progress = 0.95
                    st.session_state.progress_text = (
                        "Matching petition signatures to voter records..."
                    )
                    matching_bar.progress(
                        st.session_state.current_progress,
                        text=st.session_state.progress_text,
                    )

                    ocr_matched_df = create_ocr_matched_df(
                        ocr_df, select_voter_records, threshold=config["BASE_THRESHOLD"]
                    )

                    st.session_state.current_progress = 1.0
                    st.session_state.progress_text = "Complete!"
                    matching_bar.progress(
                        st.session_state.current_progress,
                        text=st.session_state.progress_text,
                    )

                    st.session_state.processed_results = ocr_matched_df
                    matching_bar.empty()
                    st.session_state.is_processing = False
                    st.session_state.is_processing_complete = True
                    st.session_state.processing_time = time.time() - start_time
                    st.session_state.current_progress = 0
                    st.session_state.progress_text = ""
                    st.rerun()

                except InterruptedError as e:
                    st.warning(str(e))
                    matching_bar.empty()
                    st.session_state.is_processing = False
                    st.session_state.is_processing_complete = False
                    st.session_state.current_progress = 0
                    st.session_state.progress_text = ""
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                    st.session_state.is_processing = False
                    st.session_state.is_processing_complete = False
                    st.session_state.current_progress = 0
                    st.session_state.progress_text = ""


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode("utf-8")


# Display results if available
if st.session_state.get("processed_results") is not None:
    st.markdown("### Results")

    # Update Valid column based on threshold
    results_df = st.session_state.processed_results.copy()
    results_df["Valid"] = results_df["Match Score"] >= config["BASE_THRESHOLD"]

    tabs = st.tabs(["📊 Data Table", "📈 Statistics"])
    if st.session_state.processing_time:
        st.caption(f"Processing time: {st.session_state.processing_time:.2f} seconds")

    with tabs[0]:
        edited_df = st.data_editor(
            results_df, use_container_width=True, hide_index=True
        )

    # Update the download button to use the modified dataframe
    csv = convert_df(results_df)

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="validated_petition_signatures.csv",
        mime="text/csv",
    )

    with tabs[1]:
        # results_df = st.session_state.processed_results
        col1, col2, col3 = st.columns(3)
        with col1:
            ui.metric_card(
                title="Total Records",
                content=len(results_df),
                description="Total signatures processed",
            )
        with col2:
            ui.metric_card(
                title="Valid Matches",
                content=sum(results_df["Valid"]),
                description="Signatures verified",
            )
        with col3:
            ui.metric_card(
                title="Percentage Valid",
                content=f"{(sum(results_df['Valid']) / len(results_df)) * 100:.1f}%",
                description="Percentage of signatures verified",
            )

# Add this near the bottom of your app, before the footer
st.markdown("---")
st.markdown("### Maintenance")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🗑️ Clear All Files", type="secondary", use_container_width=True):
        with st.spinner("Clearing temporary files..."):
            if wipe_all_temp_files():
                st.session_state.clear_files = True
                st.success("✅ All temporary files cleared!")
                st.info("Please refresh the page to start over.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "© 2024 Ballot Initiative Project | "
    "<a href='#'>Privacy Policy</a> | "
    "<a href='#'>Terms of Use</a>"
    "</div>",
    unsafe_allow_html=True,
)
