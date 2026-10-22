
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


ARXIV_API_URL = "https://export.arxiv.org/api/query"

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def search_papers(query: str, max_results: int = 8) -> list[dict]:
    """Search arXiv and return a list of paper metadata."""

    query = query.strip()
    if not query:
        raise ValueError("Please enter a research topic to search.")

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
        headers={"User-Agent": "RebootResearchAssistant/0.1"},
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            xml_data = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"arXiv returned HTTP {exc.code}. Please try again later."
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Could not reach arXiv. Check your internet connection and try again."
        ) from exc

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        raise RuntimeError("Could not parse the response from arXiv.") from exc

    papers = []

    for entry in root.findall("atom:entry", ATOM_NS):
        get_text = lambda tag: (
            entry.findtext(f"atom:{tag}", default="", namespaces=ATOM_NS).strip()
        )

        authors = [
            author.findtext("atom:name", default="", namespaces=ATOM_NS)
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
