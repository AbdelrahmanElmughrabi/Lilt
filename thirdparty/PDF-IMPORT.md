# PDF import dependency and limits

Selectable-text extraction uses unmodified pypdf **6.21.2**, a pure Python
BSD-3-Clause dependency. No parser extras, OCR, native PDF engine or optional
cryptography package is required or installed. Encrypted PDFs are rejected,
including those that can be opened with an empty password.

The exact wheel is pinned by URL and SHA-256 in both requirements files:
`pypdf-6.21.2-py3-none-any.whl`,
`1d44d1a3a200f25062adff0085b02040e4646431ac2ccac22e42679e91466084`.
[PyPI release metadata](https://pypi.org/pypi/pypdf/6.21.2/json).
The complete upstream license is retained in `licenses/pypdf-6.21.2-LICENSE.txt`.
The existing package notice assembler collects the installed license and the
PyInstaller spec includes its distribution metadata. No release artifact was
rebuilt as part of the source implementation batch.

Imports accept up to 20 MiB of source PDF, 200 pages and 2 MiB of extracted UTF-8
text. The escaped editable Markdown working copy must also fit within 2 MiB.
One parser worker runs at a time, with a 20-second extraction deadline and a
monitored 512 MiB RSS threshold. Workers are terminated on timeout or excessive
memory use. This process separation is not a security sandbox; memory can
overshoot the threshold between samples. A source path is never passed to the
parser. PDF JavaScript, launch actions, attachments and external links are not
executed or fetched by the import code.

Strict parsing rejects damaged or unsupported files rather than attempting
silent repair. Empty and image-only documents are rejected. Mixed PDFs retain
available selectable text; images, scans and graphical content are omitted.
Page order is retained, but columns, tables, headers, fonts and reading order
can extract imperfectly. The UI tells users to review before generating. Text
is escaped as literal content in the existing Markdown editor, without changing
the original PDF. OCR and password entry remain outside this batch.
