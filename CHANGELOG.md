# Changelog

Todos los cambios importantes de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

## [1.0.0] - 2026-11-07

Primera versión pública. Parte de la versión interna «10» del programa.

### Added
- Código dividido en módulos dentro de `src/firmador_masivo/`, instalable con `pip` y con punto de entrada `python -m firmador_masivo`.
- Suite de pruebas con `pytest`: certificados `.p12` y PDFs se generan al vuelo; incluye pruebas de la ventana (con `xvfb` en Linux) y un servidor de sello de tiempo local.
- Flujos de GitHub Actions: pruebas en cada push y, al crear una etiqueta `vX.Y.Z`, compilación del `.exe` en Windows con su SHA256 adjunto a la Release.
- Documentación: guía de usuario, cómo compilar y nota sobre validez legal.
- `README`, `CONTRIBUTING`, `SECURITY` y plantillas de issues.
- Licencia GNU AGPL-3.0.

### Changed
- La versión vive en un único lugar: `src/firmador_masivo/_version.py`.
- Los errores ya no muestran detalles técnicos ni rutas al usuario; el detalle se envía al registro de depuración.

### Fixed
- Ortografía de la interfaz y de los informes (Contraseña, posición, código, página, última…).
- Un PDF dañado, vacío o que no es un PDF ahora se informa como «El archivo está dañado o no es un PDF válido.» en lugar de «Failed to open stream».

[Unreleased]: https://github.com/ctamayoa/MassPDFSigner/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ctamayoa/MassPDFSigner/releases/tag/v1.0.0
