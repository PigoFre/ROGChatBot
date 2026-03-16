#Importing Libraries
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
#gets the analyze pdf function from the pdf analyzer, which is responsible for extracting the relevant information from the chosen PDF based on the user's request. This separation of concerns allows the PDFFinder to focus on finding the best match, while the PDFAnalyzer handles the content extraction and analysis.
from BackendsGLOBAL.PDF_Analyzer import analyze_pdf_for_request

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAI = None
#Repo Root and PDF Directory
REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = REPO_ROOT / "PDF_Database"
#Gpt model :) can be changed
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")



#Simply creating a class for the pdfs in the database, with a property to get the filename as a label.
@dataclass
class PdfCandidate:
    path: Path

    @property
    def label(self) -> str:
        return self.path.name

#Takes a list of all the pdfs in the database
def build_candidates(pdf_dir: Path) -> list[PdfCandidate]:
    candidates: list[PdfCandidate] = []
    # Funny, this is a for loop we used in class 
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        candidates.append(PdfCandidate(path=pdf_path))
    return candidates

# Calls open AI assistant to rank the possible pdfs, and returns the best match. If there is only one candidate, it returns that one without calling OpenAI.
def rank_with_openai(description: str, candidates: list[PdfCandidate]) -> PdfCandidate | None:
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed.")
    #By the way, the key is stored in a render environment variable, so it is not hardcoded anywhere in the codebase. You can set it in your local environment or in Render's dashboard.
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")
    if len(candidates) == 1:
        return candidates[0]

    client = OpenAI()
    candidate_payload = [
        {
            #list in the canidate list
            "index": index,
            #the filename, which is the label property of the PdfCandidate class
            "filename": candidate.label,
            #the full path to the pdf, which is the path property of the PdfCandidate class. This is included in the payload for transparency, but OpenAI should not rely on it for making its decision, as it may not have access to the file contents.
            "path": str(candidate.path),
        }
        for index, candidate in enumerate(candidates)
    ]
    #Returns the list of canditaes in a json format, makes it easy to parse on the OpenAI side, and also gives the user a clear view of the options. The prompt is designed to encourage OpenAI to pick the best match based on the filename meanings, without assuming access to file contents.
    prompt = (
        "Pick the single PDF that best matches the user's general description.\n"
        "Use only the filename meanings. Do not assume access to file contents.\n"
        "Return strict JSON with keys: index, reason.\n"
        "If nothing is a strong match, still choose the closest option.\n\n"
        f"User description: {description}\n\n"
        f"Candidates:\n{json.dumps(candidate_payload, indent=2)}"
    )

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=prompt,
        )
        content = response.output_text.strip()
        #I love json loads! Json loads is great for parsing the response, we now have direct access to the index of the chosen candidate and the reason for the choice, which can be useful for debugging and transparency. If parsing fails or the index is out of range, we return None to indicate that no valid choice was made.
        result = json.loads(content)
        #bang bang gets the index to teh chosen canidate, and then we just take this and pass it to the pdf analuzer
        chosen_index = int(result["index"])
        # IF the index exists, return, if not return NOTHGINGNGNGNG
        if 0 <= chosen_index < len(candidates):
            return candidates[chosen_index]
    except Exception:
        return None

    return None

#overall function that finds it, analyzes it, and returns the relevant info. It also has error handling for various edge cases, such as no request provided, no PDFs found, or OpenAI failing to choose a PDF.
def find_best_pdf(description: str) -> PdfCandidate | None:
    #if no pdf exists, we cant do anything, so we raise an error. This is a safeguard to ensure that the rest of the code has the necessary resources to function properly.
    if not PDF_DIR.exists():
        raise FileNotFoundError(f"PDF directory not found: {PDF_DIR}")
    # calls the build canidates function to get a list of all the pdfs in the database, and if there are no pdfs, we return None, which will be handled by the calling function to inform the user appropriately. This check prevents unnecessary calls to OpenAI when there are no options to choose from.
    candidates = build_candidates(PDF_DIR)
    if not candidates:
        return None
    #uses the description or what they asking for, sends it to teh ranking system, then we get the best match back, and if there is no match, we return None, which will be handled by the calling function to inform the user that OpenAI could not make a choice. This could happen if the response is not in the expected format or if there is an issue with the OpenAI API.
    return rank_with_openai(description, candidates)


def find_and_analyze_pdf(info_request: str) -> tuple[PdfCandidate, dict[str, str]] | None:
    #Uses the find best pdf to get da match.
    match = find_best_pdf(info_request)
    if match is None:
        return None
    #Uses the analyze function to get info!
    analysis = analyze_pdf_for_request(match.path, match.label, info_request)
    return match, analysis

#This is the main function that handles the entire process of receiving a user's request, finding the best matching PDF, analyzing it for the requested information, and returning the results in a structured format. It also includes error handling to provide informative feedback in case of issues at any stage of the process.
def handle_info_request(info_request: str) -> dict[str, str]:
    cleaned_request = info_request.strip()
    if not cleaned_request:
        raise ValueError("No request provided.")

    candidates = build_candidates(PDF_DIR)
    if not candidates:
        raise FileNotFoundError(f"No PDFs were found in {PDF_DIR}.")

    result = find_and_analyze_pdf(cleaned_request)
    if result is None:
        raise RuntimeError("OpenAI could not choose a PDF from the list.")

    match, analysis = result
    return {
        "request": cleaned_request,
        "match_label": match.label,
        "match_path": str(match.path),
        "citation": analysis["citation"],
        "requested_info": analysis["requested_info"],
    }


def main() -> None:
    info_request = input("What citation or info do you want? ").strip()
    try:
        result = handle_info_request(info_request)
    except Exception as exc:
        print(str(exc))
        return

    print(f"Best match: {result['match_label']}")
    print(f"Path: {result['match_path']}")
    print("Matching source: OpenAI")
    print(f"Citation: {result['citation']}")
    print(f"Requested info: {result['requested_info']}")


if __name__ == "__main__":
    main()
