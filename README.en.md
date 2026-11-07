# Mass PDF Signer

Windows desktop application that signs hundreds or thousands of PDFs in one go with one or two electronic-signature certificates (`.p12` / `.pfx`). No command line needed: pick your certificates and the folder with the PDFs, draw with the mouse where each signature goes, and press **SIGN DOCUMENTS**.

The interface is available in **Spanish, English and Portuguese (Brazil)**; switch language from the window. The project documentation in `docs/` is currently in Spanish.

## Features

- Signs with **two certificates at once** (or just one).
- **Visible signature** at the position you draw on a preview, with an optional **QR code**.
- **Avoids covering content**: detects text and images under the signature boxes and moves them to free space. If there is none, that PDF is not signed and is listed in the report.
- **Subfolders**: walks a whole tree and mirrors it in the output folder. Originals are never modified.
- **Resume**: skips what is already signed. You can also pause, resume and stop.
- Optional **timestamp** (TSA).
- **Certificate check** (password and validity) before starting.
- **Reports** on every run: `resumen_firmado_*.txt`, `registro_firmado_*.csv` (opens in Excel) and `errores_firmado.txt`.

## Install (Windows)

1. Download `FirmadorPDF.exe` and `FirmadorPDF.exe.sha256` from the **Releases** section.
2. Check the file: `(Get-FileHash .\FirmadorPDF.exe -Algorithm SHA256).Hash` must match the `.sha256` file.
3. Run `FirmadorPDF.exe`. Python is not required.

The `.exe` is not code-signed, so Windows or your antivirus may warn about it. You can build it yourself: see [docs/compilar.md](docs/compilar.md) (Spanish).

## Run from source

Requires Python 3.10+.

```bash
pip install -e .
python -m firmador_masivo
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Certificates and PDFs used by the tests are generated on the fly; the repository contains no certificates. Window tests need a display (on Linux: `xvfb-run -a pytest`).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). **Never upload your `.p12`/`.pfx` files, passwords or real PDFs to an issue or pull request.**

## License

[GNU AGPL-3.0](LICENSE). It is AGPL because the program bundles [PyMuPDF](https://pymupdf.readthedocs.io/), which is AGPL-3.0.

## Disclaimer

The program applies digital signatures with the certificate you provide; it does not issue certificates and is not a certification authority. The legal validity of a signature depends on the certificate used and on applicable law. This is not legal advice.
