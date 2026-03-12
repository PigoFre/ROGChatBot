
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from BackendsGLOBAL.PDF_Analyzer import analyze_pdf_for_request

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAI = None

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = REPO_ROOT / "PDF_Database"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@dataclass
class PdfCandidate:
    path: Path

    @property
    def label(self) -> str:
        return self.path.name


def build_candidates(pdf_dir: Path) -> list[PdfCandidate]:
    candidates: list[PdfCandidate] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        candidates.append(PdfCandidate(path=pdf_path))
    return candidates


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
