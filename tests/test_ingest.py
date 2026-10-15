from tourist_assistant.config import get_settings
from tourist_assistant.ingest import chunk_by_place, chunk_recursive, load_pdf_lines


def _lines():
    return load_pdf_lines(get_settings().pdf_path)


def test_loader_merges_orphan_bullets():
    lines = _lines()
    assert lines and all(line.text not in {"-", "o", "•", "▪"} for line in lines)
    assert {line.page for line in lines} <= set(range(1, 26))


def test_chunk_by_place_covers_known_places_with_metadata():
    chunks = chunk_by_place(_lines())
    places = {c.metadata["place"] for c in chunks}
    assert {"Santa Cruz de Tenerife", "El Teide", "Masca"} <= places
    teide = next(c for c in chunks if c.metadata["place"] == "El Teide")
    assert teide.metadata["zone"] == "Zona Norte"
    assert teide.metadata["page_start"] == 15
    assert "Mirador de La Tarta" in teide.text
    assert not teide.text.startswith("[Zona Norte · El Teide]\n•")
    assert all(c.text and c.metadata["page_start"] <= c.metadata["page_end"] for c in chunks)


def test_long_food_section_is_split_per_restaurant():
    chunks = chunk_by_place(_lines())
    food = [c for c in chunks if c.metadata["place"].startswith("Sitios para comer")]
    assert len(food) > 5
    assert any("Guachinche El Cubano" in c.metadata["place"] for c in food)


def test_links_are_stripped():
    assert all(
        "[ubicación]" not in c.text and "[vídeo" not in c.text for c in chunk_by_place(_lines())
    )


def test_recursive_chunks_respect_size():
    chunks = chunk_recursive(_lines(), size=500, overlap=100)
    assert len(chunks) > 20
    assert all(1 <= c.metadata["page_start"] <= c.metadata["page_end"] <= 25 for c in chunks)
    assert all(len(c.text) <= 500 for c in chunks)
