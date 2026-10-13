"""Tiny synthetic specifications for native extraction tests; no office automation."""
import json
import pathlib
import zipfile

MARKER = "DA_DOCUMENT_SPEC_7A3"


def create_fixtures(root):
    root = pathlib.Path(root)
    root.mkdir(parents=True, exist_ok=True)
    text = MARKER + "\nAcceptance: local extraction; no macro execution."
    (root / "spec.md").write_text("# Specification\n" + text, encoding="utf-8")
    (root / "spec.json").write_text(json.dumps({"title": MARKER, "acceptance": "local extraction"}), encoding="utf-8")
    (root / "spec.yaml").write_text("title: " + MARKER + "\nacceptance: local extraction\n", encoding="utf-8")
    (root / "spec.rtf").write_text(r"{\rtf1\ansi " + MARKER + r"\par Acceptance: local extraction.}", encoding="ascii")
    with zipfile.ZipFile(root / "spec.docx", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + MARKER + '</w:t></w:r></w:p><w:p><w:r><w:t>Acceptance: local extraction.</w:t></w:r></w:p></w:body></w:document>')
    with zipfile.ZipFile(root / "spec.xlsx", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>')
        z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Requirements" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>' + MARKER + '</t></is></c><c r="B1" t="inlineStr"><is><t>Acceptance</t></is></c></row></sheetData></worksheet>')
    content = ("BT /F1 12 Tf 50 750 Td (" + MARKER + ") Tj 0 -20 Td (Acceptance: local extraction.) Tj ET").encode("ascii")
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream"]
    pdf = bytearray(b"%PDF-1.4\n"); offsets = [0]
    for n, obj in enumerate(objects, 1):
        offsets.append(len(pdf)); pdf += str(n).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(pdf)
    pdf += b"xref\n0 6\n0000000000 65535 f \n"
    for pos in offsets[1:]: pdf += (f"{pos:010d} 00000 n \n").encode()
    pdf += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"
    (root / "spec.pdf").write_bytes(pdf)
    return root


if __name__ == "__main__":
    import sys
    create_fixtures(sys.argv[1])
