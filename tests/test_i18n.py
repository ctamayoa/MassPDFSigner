import json
import re
import string
from importlib import resources
from pathlib import Path

import pymupdf
import pytest

from conftest import CLAVE, crear_pdf
from firmador_masivo import i18n
from firmador_masivo.firmas import cargar_firmante, firmar_un_pdf, revisar_firma
from firmador_masivo.i18n import IDIOMAS, t

RAIZ = Path(__file__).resolve().parent.parent / "src" / "firmador_masivo"


def _marcadores(texto):
    return sorted(n for _, n, _, _ in string.Formatter().parse(texto) if n)


@pytest.mark.parametrize("cod", [c for c in IDIOMAS if c != "es"])
def test_mismas_claves_y_marcadores_que_el_espanol(cod):
    base, otro = i18n.claves("es"), i18n.claves(cod)
    assert set(otro) == set(base), (set(base) ^ set(otro))
    for clave, texto in base.items():
        if clave.startswith("sello.texto"):
            assert "%(signer)s" in otro[clave]
            continue
        assert _marcadores(otro[clave]) == _marcadores(texto), clave
        assert otro[clave].strip(), clave


@pytest.mark.parametrize("cod", list(IDIOMAS))
def test_todos_los_json_son_validos_y_sin_valores_vacios(cod):
    texto = resources.files("firmador_masivo.idiomas").joinpath(f"{cod}.json").read_text(encoding="utf-8")
    datos = json.loads(texto)
    assert all(isinstance(v, str) and v for v in datos.values())


def test_todas_las_claves_usadas_en_el_codigo_existen():
    usadas = set()
    for py in RAIZ.glob("*.py"):
        usadas |= set(re.findall(r'\bt\("([a-z0-9_.]+)"', py.read_text(encoding="utf-8")))
    assert usadas
    assert usadas <= set(i18n.claves("es")), usadas - set(i18n.claves("es"))


def test_claves_sin_uso_no_se_acumulan():
    codigo = "\n".join(p.read_text(encoding="utf-8") for p in RAIZ.glob("*.py"))
    sin_uso = [k for k in i18n.claves("es") if f'"{k}"' not in codigo]
    assert sin_uso == []


def test_t_con_marcadores_y_codigo_desconocido():
    i18n.fijar_idioma("en")
    assert t("estado.firmando", i=2, total=5, nombre="x.pdf") == "Signing 2 of 5: x.pdf"
    i18n.fijar_idioma("xx")                      # código desconocido: vuelve al español
    assert i18n.idioma_actual() == "es"


def test_clave_faltante_en_otro_idioma_usa_espanol(monkeypatch):
    datos = dict(i18n.claves("en"))
    del datos["ui.firmar"]
    monkeypatch.setitem(i18n._cache, "en", datos)
    i18n.fijar_idioma("en")
    assert t("ui.firmar") == "FIRMAR DOCUMENTOS"


def test_deteccion_por_variable_lang(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("LC_ALL", raising=False)
    for lang, esperado in (("pt_BR.UTF-8", "pt"), ("en_US.UTF-8", "en"), ("es_EC.UTF-8", "es"), ("fr_FR", "es"), ("", "es")):
        monkeypatch.setenv("LANG", lang)
        assert i18n.detectar_idioma() == esperado


def test_preferencia_guardada(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRMADOR_CONFIG_DIR", str(tmp_path))
    i18n.guardar_preferencia("pt")
    assert i18n.iniciar() == "pt"
    (tmp_path / "config.json").write_text("{roto", encoding="utf-8")   # config dañada: no falla
    monkeypatch.setattr(i18n, "detectar_idioma", lambda: "en")
    assert i18n.iniciar() == "en"


@pytest.mark.parametrize("cod,frase", [
    ("es", "Firmado electrónicamente por"),
    ("en", "Electronically signed by"),
    ("pt", "Assinado eletronicamente por"),
])
@pytest.mark.parametrize("qr", [False, True])
def test_texto_de_la_firma_sigue_el_idioma(tmp_path, certs, cod, frase, qr):
    i18n.fijar_idioma(cod)
    s = cargar_firmante(certs["tilde"], CLAVE)
    pdf = crear_pdf(tmp_path / "a.pdf")
    salida = str(tmp_path / "f.pdf")
    firmar_un_pdf(pdf, salida, [(s, "Firma1", (40, 40, 285, 115))], -1, True, None, qr)
    texto = pymupdf.open(salida)[-1].get_text()
    assert frase in texto and "José Muñoz Peña" in texto


def test_firma_propia_se_reconoce_en_todos_los_idiomas():
    """Un PDF ya firmado con el programa en cualquier idioma: sus marcas no cuentan como contenido."""
    from firmador_masivo.posicion import _marcas_de_sello
    marcas = _marcas_de_sello()
    for esperada in ("Firmado electr", "Electronically signed", "Assinado eletronicamente"):
        assert esperada in marcas


def test_mensajes_de_revision_en_cada_idioma(certs):
    esperado = {"es": "VENCIDA", "en": "EXPIRED", "pt": "VENCIDA"}
    for cod, palabra in esperado.items():
        i18n.fijar_idioma(cod)
        ok, texto = revisar_firma(certs["vencida"], CLAVE)
        assert not ok and palabra in texto
