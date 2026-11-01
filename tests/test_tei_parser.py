from epistemis.preprocessor import build_blocks_from_tei, parse_tei


def test_parse_tei_extracts_sections_paragraphs_and_citations(tmp_path):
    tei = """<?xml version="1.0" encoding="UTF-8"?>
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
      <text>
        <body>
          <div>
            <head>Introduction</head>
            <p>Evidence is discussed here <ref type="bibr">[1]</ref>.</p>
          </div>
        </body>
      </text>
    </TEI>
    """
    path = tmp_path / "sample.tei.xml"
    path.write_text(tei, encoding="utf-8")

    sections = parse_tei(str(path))
    blocks = build_blocks_from_tei(sections)

    assert len(sections) == 1
    assert sections[0]["section_title"] == "introduction"
    assert sections[0]["paragraphs"][0]["has_citation"] is True
    assert "[1]" in sections[0]["paragraphs"][0]["citations"]
    assert len(blocks) == 1
    assert blocks[0]["block_type"] == "paragraph"
