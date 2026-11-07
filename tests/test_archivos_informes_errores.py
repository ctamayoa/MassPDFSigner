import csv
import os
import re
import time

import pytest

import firmador_masivo
from firmador_masivo import errores
from firmador_masivo.archivos import listar_pdfs, ruta_larga
from firmador_masivo.i18n import t
from firmador_masivo.informes import armar_resumen, fmt_hms, guardar_informes, resumen_corto


# ---------------------------------------------------------------- versión
def test_version_semver_y_unica():
    assert re.fullmatch(r"\d+\.\d+\.\d+", firmador_masivo.__version__)
    assert firmador_masivo.__version__ == "1.0.0"


# ---------------------------------------------------------------- archivos
def _arbol(base):
    for rel in ("A001 Factura/doc1.pdf", "A002 Importación/doc2.pdf", "B/C/D profunda/doc3.pdf",
                "G mayúsculas/DOC4.PDF", "salida/ya.pdf", "raiz.pdf", "A001 Factura/nota.txt"):
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    (base / "F sin pdfs").mkdir()


def test_listar_no_recursivo(tmp_path):
    _arbol(tmp_path)
    assert listar_pdfs(str(tmp_path), str(tmp_path / "salida"), False) == ["raiz.pdf"]


def test_listar_recursivo_ignora_salida_y_no_pdf(tmp_path):
    _arbol(tmp_path)
    lista = listar_pdfs(str(tmp_path), str(tmp_path / "salida"), True)
    assert len(lista) == 5
    assert not any(r.startswith("salida") for r in lista)
    assert not any(r.endswith(".txt") for r in lista)
    assert any(r.endswith("DOC4.PDF") for r in lista)


def test_listar_carpeta_inexistente(tmp_path):
    assert listar_pdfs(str(tmp_path / "nada"), "", True) == []


@pytest.mark.skipif(os.name != "nt", reason="el prefijo largo solo aplica en Windows")
def test_ruta_larga_agrega_prefijo():
    corta = ruta_larga("C:\\carpeta\\a.pdf")
    assert not corta.startswith("\\\\?\\")
    larga = ruta_larga("C:\\" + "x" * 250 + "\\a.pdf")
    assert larga.startswith("\\\\?\\C:\\")


# ---------------------------------------------------------------- informes
def _estadisticas(tmp_path):
    t = time.time()
    reg = [
        {"archivo": "a/uno.pdf", "estado": "firmado", "segundos": 0.2, "kb": 120.0, "hora": t, "mensaje": "", "ajuste": None},
        {"archivo": "a/dos.pdf", "estado": "firmado", "segundos": 0.4, "kb": 80.0, "hora": t, "mensaje": "", "ajuste": 18},
        {"archivo": "b/tres.pdf", "estado": "omitido", "segundos": 0.0, "kb": 10.0, "hora": t, "mensaje": "", "ajuste": None},
        {"archivo": "b/cuatro.pdf", "estado": "error", "segundos": 0.1, "kb": 1.0, "hora": t,
         "mensaje": t("error.danado"), "ajuste": None},
        {"archivo": "b/cinco.pdf", "estado": "sin_espacio", "segundos": 0.1, "kb": 5.0, "hora": t,
         "mensaje": "No hay espacio libre para las firmas en la página 1", "ajuste": None},
    ]
    return {"inicio": t - 60, "fin": t, "pausa_s": 5, "detenido": False, "total": 6, "registros": reg,
            "visible": True, "qr": True, "pagina": "última", "tsa": None, "recursivo": True, "evitar": True,
            "entrada": str(tmp_path / "in"), "salida": str(tmp_path), "equipo": "EQUIPO", "usuario": "usuario",
            "firmantes": [("Firma 1", "Firmante Uno", "01/01/2099")]}


def test_fmt_hms():
    assert fmt_hms(3725) == "01:02:05"
    assert fmt_hms(-4) == "00:00:00"


def test_resumen_contenido(tmp_path):
    e = _estadisticas(tmp_path)
    txt = armar_resumen(e)
    assert f"v{firmador_masivo.__version__}" in txt
    assert "Firmados            : 2" in txt
    assert "Con posición ajustada: 1" in txt
    assert "Pendientes          : 1" in txt
    assert "SIN ESPACIO (no firmados): 1" in txt
    assert "b/cuatro.pdf: El archivo está dañado" in txt
    corto = resumen_corto(e)
    assert "Firmados: 2" in corto and "Pendientes: 1" in corto and "ver el CSV" in corto


def test_resumen_sin_firmados(tmp_path):
    e = _estadisticas(tmp_path)
    e["registros"] = []
    assert "no se firmó ningún PDF" in armar_resumen(e)


def test_guardar_informes_csv(tmp_path):
    ruta_txt, ruta_csv = guardar_informes(_estadisticas(tmp_path))
    assert os.path.basename(ruta_txt).startswith("resumen_firmado_")
    assert os.path.basename(ruta_csv).startswith("registro_firmado_")
    with open(ruta_csv, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.reader(f, delimiter=";"))
    assert filas[0][:4] == ["hora_fin", "carpeta", "archivo", "estado"]
    por_archivo = {f[2]: f for f in filas[1:]}
    assert por_archivo["dos.pdf"][4] == "ajustada" and por_archivo["dos.pdf"][5] == "18"
    assert por_archivo["uno.pdf"][4] == "original"
    assert por_archivo["cinco.pdf"][3] == "sin_espacio"
    assert por_archivo["cinco.pdf"][4] == "SIN ESPACIO - NO FIRMADO"
    assert por_archivo["uno.pdf"][6] == "0,20"      # coma decimal para Excel en español


# ---------------------------------------------------------------- errores
@pytest.mark.parametrize("exc,esperado", [
    (RuntimeError("Failed to open stream"), t("error.danado")),
    (RuntimeError("Illegal PDF header"), t("error.danado")),
    (RuntimeError("Could not read malformed PDF file"), t("error.danado")),
    (RuntimeError("File has not been decrypted"), t("error.cifrado")),
    (PermissionError("denegado: C:\\secreto\\x.pdf"), t("error.acceso")),
    (FileNotFoundError("C:\\secreto\\x.pdf"), t("error.no_existe")),
    (ValueError("algo raro interno"), t("error.generico")),
])
def test_describir_error(exc, esperado):
    texto = errores.describir_error(exc)
    assert texto == esperado
    assert "secreto" not in texto and "stream" not in texto.lower()


def test_pyhanko_pdf_danado_se_traduce(tmp_path):
    import io

    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    for contenido in (b"esto no es un pdf", b"%PDF-1.4\nbasura", b""):
        with pytest.raises(Exception) as e:
            IncrementalPdfFileWriter(io.BytesIO(contenido), strict=False)
        assert errores.describir_error(e.value) == t("error.danado")
