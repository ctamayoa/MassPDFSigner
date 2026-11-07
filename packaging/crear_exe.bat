@echo off
rem Ejecutar desde la raiz del repositorio. El .exe queda en dist\FirmadorPDF.exe
echo Instalando dependencias...
pip install -e . pyinstaller
echo Creando ejecutable...
pyinstaller --onefile --windowed --name FirmadorPDF --paths src --collect-all pyhanko --collect-all pyhanko_certvalidator --collect-all pymupdf --collect-all aiohttp --collect-all qrcode --collect-data firmador_masivo packaging\firmador_pdf.py
echo Listo. El ejecutable queda en dist\FirmadorPDF.exe
pause
