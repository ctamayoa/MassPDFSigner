@echo off
rem Ejecutar desde la raiz del repositorio. Genera la carpeta dist\FirmadorPDF\ (programa sin instalar).
rem El instalador se arma despues con Inno Setup: ISCC.exe /DAppVersion=X.Y.Z packaging\instalador.iss
echo Instalando dependencias...
pip install -e . pyinstaller
echo Creando el programa...
pyinstaller --noconfirm --windowed --name FirmadorPDF --paths src --collect-all pyhanko --collect-all pyhanko_certvalidator --collect-all aiohttp --collect-all qrcode --collect-binaries pymupdf --collect-data firmador_masivo --exclude-module onnxruntime --exclude-module numpy --exclude-module networkx --exclude-module pandas --exclude-module scipy --exclude-module matplotlib --exclude-module pymupdf.layout --exclude-module pymupdf4llm --exclude-module pymupdf_layout packaging\firmador_pdf.py
echo Listo. El programa queda en dist\FirmadorPDF\FirmadorPDF.exe
pause
