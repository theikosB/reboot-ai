
import io
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

USER_AGENT = "RebootResearchAssistant/0.2"
MAX_PDF_BYTES = 10 * 1024 * 1024


def search_papers(query: str, max_results: int = 8) -> list[dict]:
    """Search arXiv and return paper metadata and links."""

    query = query.strip()
    if not query:
        raise ValueError("Please enter a research topic to search.")

    query = query[:200]
    max_results = max(1, min(max_results, 10))

    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })

    request = urllib.request.Request(
        f"{ARXIV_API_URL}?{params}",
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            xml_data = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"arXiv returned HTTP {exc.code}. Please try again later."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(
            "Could not reach arXiv. Check your internet connection and try again."
        ) from exc

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        raise RuntimeError("Could not parse the response from arXiv.") from exc

    papers = []

    for entry in root.findall("atom:entry", ATOM_NS):
        def get_text(tag):
            return entry.findtext(
                f"atom:{tag}", default="", namespaces=ATOM_NS
            ).strip()

        authors = [
            author.findtext(
                "atom:name", default="", namespaces=ATOM_NS
            )
            for author in entry.findall("atom:author", ATOM_NS)
        ]

        paper_url = get_text("id")
        pdf_url = next(
            (
                link.attrib["href"]
                for link in entry.findall("atom:link", ATOM_NS)
                if link.attrib.get("title") == "pdf"
            ),
            "",
        )

        papers.append({
            "title": " ".join(get_text("title").split()),
            "authors": authors,
            "abstract": " ".join(get_text("summary").split()),
            "published": get_text("published")[:10],
            "url": paper_url,
            "pdf_url": pdf_url or paper_url.replace("/abs/", "/pdf/"),
        })

    return papers


def fetch_paper_text(
    paper: dict,
    max_pages: int = 6,
    max_chars: int = 8000,
) -> dict:
    """
    Extract a bounded excerpt from an arXiv PDF.

    Returns status and extracted text. Never assumes the entire paper
    has been read; only the selected opening pages are extracted.
    """

    pdf_url = paper.get("pdf_url", "")
    host = urlparse(pdf_url).hostname or ""

    if host not in {"arxiv.org", "www.arxiv.org"}:
        return {
            "status": "unavailable",
            "text": "",
            "reason": "PDF URL was not on an approved arXiv host.",
        }

    request = urllib.request.Request(
        pdf_url,
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            pdf_bytes = response.read(MAX_PDF_BYTES + 1)
    except (urllib.error.URLError, urllib.error.HTTPError,
            TimeoutError, OSError) as exc:
        return {
            "status": "unavailable",
            "text": "",
            "reason": f"PDF download failed: {type(exc).__name__}",
        }

    if len(pdf_bytes) > MAX_PDF_BYTES:
        return {
            "status": "unavailable",
            "text": "",
            "reason": "PDF exceeds the 10 MB download limit.",
        }

    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))

        extracted_pages = []
        for page in reader.pages[:max(1, min(max_pages, 8))]:
            extracted_pages.append(page.extract_text() or "")

        text = "\n\n".join(extracted_pages).strip()[:max_chars]

        if not text:
            return {
                "status": "unavailable",
                "text": "",
                "reason": "No extractable text found; the PDF may be scanned.",
            }

        return {
            "status": "partial",
            "text": text,
            "reason": (
                f"Extracted up to {min(max_pages, 8)} opening pages; "
                "this is not a complete paper review."
            ),
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "text": "",
            "reason": f"PDF text extraction failed: {type(exc).__name__}",
        }
