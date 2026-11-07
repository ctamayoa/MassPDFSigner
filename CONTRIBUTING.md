# Cómo contribuir

Gracias por querer ayudar. Este documento resume lo necesario para proponer cambios.

## Preparar el entorno

```bash
git clone <URL-del-repositorio>
cd <carpeta>
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

## Ejecutar las pruebas

```bash
pytest
```

Las pruebas de la ventana (`tests/test_gui.py`) necesitan pantalla. En Linux:

```bash
sudo apt-get install -y xvfb python3-tk
xvfb-run -a pytest
```

Todo cambio debe dejar las pruebas en verde. Si corriges un error, añade una prueba que falle sin la corrección.

## Reglas del proyecto

- **Idioma**: interfaz, documentación y mensajes en español, con tildes y eñes correctas.
- **Datos reales, nunca**: ni certificados `.p12`/`.pfx`, contraseñas, nombres de firmantes reales, PDFs reales, rutas de tu equipo ni datos de clientes, ni en el código, ni en las pruebas, ni en capturas, ni en el historial de git. Las pruebas generan sus certificados al vuelo (ver `tests/conftest.py`).
- **Sin referencias a terceros** en la interfaz, en el texto de la firma ni en el QR.
- **Mensajes al usuario**: lenguaje llano, sin rutas, sin trazas ni errores técnicos crudos. Usa `describir_error()` de `errores.py`.
- **Hilos**: nunca leas variables de Tk desde el hilo de trabajo; cópialas antes a un diccionario.
- **Versión**: se cambia solo en `src/firmador_masivo/_version.py`.
- **Dependencia AGPL**: PyMuPDF es AGPL-3.0, por eso el proyecto lo es. No agregues dependencias con licencias incompatibles.

## Idiomas

Los textos de la interfaz están en `src/firmador_masivo/idiomas/` (`es.json`, `en.json`, `pt.json`). El español es el idioma base.

- Todo texto nuevo va como clave en `es.json` y se usa con `t("clave")` (nunca escrito directo en el código).
- Agrega la misma clave, con los mismos marcadores `{nombre}`, en los demás archivos. Las pruebas fallan si falta alguna o si sobra una clave sin usar.
- Para añadir un idioma: crea `idiomas/<código>.json` con todas las claves y agrega el código a `IDIOMAS` en `i18n.py`.
- Los encabezados y estados del CSV (`firmado`, `omitido`, `error`, `sin_espacio`) no se traducen.

## Enviar un cambio

1. Crea una rama a partir de `main`.
2. Haz commits pequeños con mensajes claros.
3. Actualiza `CHANGELOG.md` bajo `[Unreleased]`.
4. Abre el pull request y describe qué cambia y cómo lo probaste.

## Publicar una versión (mantenedores)

1. Sube la versión en `_version.py` y pasa lo de `[Unreleased]` a una sección nueva en `CHANGELOG.md`.
2. Haz merge a `main` con el CI en verde.
3. Crea y sube la etiqueta: `git tag vX.Y.Z && git push origin vX.Y.Z`. El flujo `release` compila el `.exe`, calcula su SHA256 y los adjunta a la Release.
