from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAI = None


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
#Parses the open ai response to ensure we get the json content we expect, even if the model wraps it in code fences or includes additional text. It first tries to parse the entire response as JSON, and if that fails, it looks for JSON within code fences or standalone JSON objects in the response.

def parse_json_response(content: str) -> dict[str, str]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if fenced_match:
            return json.loads(fenced_match.group(1))

        object_match = re.search(r"\{.*\}", content, re.DOTALL)
        if object_match:
            return json.loads(object_match.group(0))

        raise RuntimeError("OpenAI returned a response that was not valid JSON.")

#Uses pydf package to extract text from the first few pages of the PDF, up to a specified character limit. It handles cases where text extraction might fail and ensures that we get a reasonable excerpt for analysis.

def extract_pdf_excerpt(pdf_path: Path, char_limit: int = 4000) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("The pypdf package is not installed.")

    try:
        reader = PdfReader(str(pdf_path))
        excerpt_parts: list[str] = []
        current_length = 0

        for page in reader.pages[:4]:
            text = (page.extract_text() or "").strip()
            if not text:
                continue

            remaining = char_limit - current_length
            if remaining <= 0:
                break

            excerpt = text[:remaining]
            excerpt_parts.append(excerpt)
            current_length += len(excerpt)

        return "\n".join(excerpt_parts).strip()
    except Exception as exc:  # pragma: no cover - depends on PDF contents
        raise RuntimeError(f"Could not extract text from {pdf_path.name}.") from exc

#Finds the analysis, than returns the citation and the requested info as a dictionary. It uses the extracted text from the PDF and the user's request to generate a response from OpenAI, which is then parsed to extract the relevant information.
def analyze_pdf_for_request(pdf_path: Path, pdf_label: str, info_request: str) -> dict[str, str]:
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed.")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set.")

    excerpt = extract_pdf_excerpt(pdf_path)
    if not excerpt:
        raise RuntimeError(f"No readable text could be extracted from {pdf_path.name}.")

    client = OpenAI()
    prompt = (
        "You are analyzing one academic PDF.\n"
        "Use the extracted text to answer the user's request about this paper.\n"
        "Return strict JSON with keys: citation, requested_info.\n\n"
        f"User request: {info_request}\n\n"
        f"Selected PDF filename: {pdf_label}\n\n"
        f"Extracted PDF text:\n{excerpt}"
    )

    response = client.responses.create(
        model=DEFAULT_MODEL,
        input=prompt,
    )
    content = response.output_text.strip()
    result = parse_json_response(content)
    return {
        "citation": str(result.get("citation", "")).strip(),
        "requested_info": str(result.get("requested_info", "")).strip(),
    }
