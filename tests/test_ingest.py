from tourist_assistant.config import get_settings
from tourist_assistant.ingest import chunk_by_place, chunk_recursive, load_pdf_lines


def _lines():
    return load_pdf_lines(get_settings().pdf_path)


def test_chunk_by_place_has_metadata_and_clean_text():
    docs = chunk_by_place(_lines())
    places = {d.metadata["place"] for d in docs}
    assert {"Santa Cruz de Tenerife", "El Teide", "Masca"} <= places
    teide = next(d for d in docs if d.metadata["place"] == "El Teide")
    assert teide.metadata["zone"] == "Zona Norte" and teide.metadata["page_start"] == 15
    assert "Mirador de La Tarta" in teide.page_content
    assert all("[ubicación]" not in d.page_content for d in docs)


def test_food_section_is_split_per_restaurant():
    docs = chunk_by_place(_lines())
    assert any("Guachinche El Cubano" in d.metadata["place"] for d in docs)


def test_recursive_chunks_respect_size_and_pages():
    docs = chunk_recursive(_lines(), size=500, overlap=100)
    assert all(len(d.page_content) <= 500 for d in docs)
    assert all(1 <= d.metadata["page_start"] <= d.metadata["page_end"] <= 25 for d in docs)
