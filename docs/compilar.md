# Cómo compilar

## Ejecutar sin compilar

Requiere Python 3.10 o superior.

```bash
pip install -e .
python -m firmador_masivo
```

## Compilar el `.exe` en Windows

Desde la raíz del repositorio:

```powershell
pip install -e . pyinstaller
pyinstaller --onefile --windowed --name FirmadorPDF --paths src --collect-all pyhanko --collect-all pyhanko_certvalidator --collect-all pymupdf --collect-all aiohttp --collect-all qrcode --collect-data firmador_masivo packaging/firmador_pdf.py
```

El resultado queda en `dist\FirmadorPDF.exe`. También puedes ejecutar `packaging\crear_exe.bat`, que hace lo mismo.

Notas:

- `packaging/firmador_pdf.py` es un archivo mínimo que solo llama a `firmador_masivo.gui.main()`. Se usa en lugar de `python -m` porque PyInstaller necesita un script como punto de entrada.
- Cada `--collect-all` incluye los archivos de datos de esa librería; sin ellos el `.exe` falla al arrancar.
- Compila con la misma versión de Python con la que vas a distribuir (el flujo de GitHub usa 3.13).

## Comprobar el resultado

Calcula el SHA256 para compararlo con el publicado en la Release:

```powershell
(Get-FileHash .\dist\FirmadorPDF.exe -Algorithm SHA256).Hash
```

Dos compilaciones del mismo código en máquinas distintas pueden dar hashes diferentes; la comparación es válida contra el archivo que descargas de la Release, no contra uno compilado por ti.

## Publicar una versión (mantenedores)

La compilación oficial la hace GitHub Actions al subir una etiqueta:

1. Cambia la versión en `src/firmador_masivo/_version.py` (único lugar).
2. En `CHANGELOG.md`, mueve lo de `[Unreleased]` a una sección nueva con la versión y la fecha.
3. Haz merge a `main` con el CI en verde.
4. Crea y sube la etiqueta:

   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

El flujo `.github/workflows/release.yml` comprueba que la etiqueta coincide con `_version.py`, corre las pruebas, compila el `.exe` en Windows, calcula su SHA256 y publica ambos en la Release, con las notas tomadas del `CHANGELOG`.

## Si el antivirus bloquea el `.exe`

Un ejecutable de PyInstaller sin firma digital suele generar falsos positivos. Opciones: compilarlo tú mismo desde el código, o distribuir el programa como código fuente. Existen programas de firma de código gratuitos para proyectos de código abierto (por ejemplo, SignPath Foundation); este proyecto aún no los usa.
