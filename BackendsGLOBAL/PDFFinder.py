
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path
from PDF_Analyzer import analyze_pdf_for_request
#openai is an optional dependency, so we handle the ImportError gracefully. If the package is not installed, we set OpenAI to None and raise a RuntimeError when it's used.
try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAI = None

# Constants, or the roots of the database and the default model to use for ranking. The PDF_DIR is set to a "PDF_Database" folder located at the root of the repository, and the DEFAULT_MODEL is determined by an environment variable with a fallback to "gpt-4o-mini".

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = REPO_ROOT / "PDF_Database"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

#Data Class that Stores the path of the PDF and has a property to return the filename as a label
@dataclass
class PdfCandidate:
    path: Path

    @property
    def label(self) -> str:
        return self.path.name

#Builds list of candidates by scanning the PDF directory and creating a PdfCandidate for each PDF file found. It sorts the files alphabetically to ensure consistent ordering.

def build_candidates(pdf_dir: Path) -> list[PdfCandidate]:
    candidates: list[PdfCandidate] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        candidates.append(PdfCandidate(path=pdf_path))
    return candidates

#Uses what we gained above in pdf canidated and teh built list from build_candidates to rank the best match using openai

def rank_with_openai(description: str, candidates: list[PdfCandidate]) -> PdfCandidate | None:
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed.")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")
    if len(candidates) == 1:
        return candidates[0]

    client = OpenAI()
    candidate_payload = [
        {
            "index": index,
            "filename": candidate.label,
            "path": str(candidate.path),
        }
        for index, candidate in enumerate(candidates)
    ]

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
        result = json.loads(content)
        chosen_index = int(result["index"])
        if 0 <= chosen_index < len(candidates):
            return candidates[chosen_index]
    except Exception:
        return None

    return None
#mAKES SURE THAT THE PDF DIRECTORY EXISTS, BUILDS THE CANDIDATES, AND RANKS THEM USING OPENAI. It returns the best match or None if no candidates are found or if an error occurs during ranking

def find_best_pdf(description: str) -> PdfCandidate | None:
    if not PDF_DIR.exists():
        raise FileNotFoundError(f"PDF directory not found: {PDF_DIR}")

    candidates = build_candidates(PDF_DIR)
    if not candidates:
        return None

    return rank_with_openai(description, candidates)


def find_and_analyze_pdf(info_request: str) -> tuple[PdfCandidate, dict[str, str]] | None:
    match = find_best_pdf(info_request)
    if match is None:
        return None

    analysis = analyze_pdf_for_request(match.path, match.label, info_request)
    return match, analysis

#The main function prompts the user for a description of citation, finds the best match using the find_best_pdf function, and prints the result. It also handles cases where no description is provided or when no PDFs are found.
def main() -> None:
    info_request = input("What citation or info do you want? ").strip()
    if not info_request:
        print("No request provided.")
        return

    candidates = build_candidates(PDF_DIR)
    if not candidates:
        print(f"No PDFs were found in {PDF_DIR}.")
        return

    print("Available PDFs:")
    for candidate in candidates:
        print(f"- {candidate.label}")

    result = find_and_analyze_pdf(info_request)
    if result is None:
        print("OpenAI could not choose a PDF from the list.")
        return

    match, analysis = result

    print(f"Best match: {match.label}")
    print(f"Path: {match.path}")
    print("Matching source: OpenAI")
    print(f"Citation: {analysis['citation']}")
    print(f"Requested info: {analysis['requested_info']}")


if __name__ == "__main__":
    main()
