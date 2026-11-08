"""Verificación de firmas de PDFs ya firmados."""
import csv

import pymupdf
import pytest
from asn1crypto import pem

from conftest import CLAVE, crear_pdf
from firmador_masivo.firmas import cargar_firmante, firmar_un_pdf
from firmador_masivo.validacion import (aplanar, cargar_raices, guardar_csv, verificar_pdf,
                                        veredicto_de)

CAJA1 = (40, 40, 285, 115)
CAJA2 = (310, 40, 555, 115)


def firmado(tmp_path, certs, *nombres, nombre_pdf="f.pdf"):
    pdf = crear_pdf(tmp_path / "base.pdf")
    destino = str(tmp_path / nombre_pdf)
    cajas = [CAJA1, CAJA2]
    firmantes = [(cargar_firmante(certs[n], CLAVE), f"Firma{i}", cajas[i - 1])
                 for i, n in enumerate(nombres, 1)]
    firmar_un_pdf(pdf, destino, firmantes, -1, True)
    return destino


def carpeta_raiz(tmp_path, certs, nombre, formato="pem"):
    d = tmp_path / f"raices_{formato}"
    d.mkdir(exist_ok=True)
    cert = cargar_firmante(certs[nombre], CLAVE).signing_cert
    if formato == "pem":
        (d / "emisor.pem").write_bytes(pem.armor("CERTIFICATE", cert.dump()))
    else:
        (d / "emisor.cer").write_bytes(cert.dump())
    return str(d)


# ----------------------------------------------------------------- firmas
def test_firma_integra_sin_raices_no_verifica_emisor(tmp_path, certs):
    res = verificar_pdf(firmado(tmp_path, certs, "uno"))
    f = res["firmas"][0]
    assert res["error"] is None and len(res["firmas"]) == 1
    assert f["firmante"] == "Firmante Uno" and f["campo"] == "Firma1"
    assert f["integridad"] and f["cambios"] == "ninguno" and f["vigente"]
    assert f["confianza"] == "sin_raices" and f["veredicto"] == "integra"
    assert f["fecha"] is not None and f["sello"] is None


@pytest.mark.parametrize("formato", ["pem", "der"])
def test_con_raiz_correcta_es_valida(tmp_path, certs, formato):
    raices, leidos, ilegibles = cargar_raices(carpeta_raiz(tmp_path, certs, "uno", formato))
    assert (leidos, ilegibles) == (1, 0)
    f = verificar_pdf(firmado(tmp_path, certs, "uno"), raices)["firmas"][0]
    assert f["confianza"] == "confiable" and f["veredicto"] == "valida"


def test_con_raiz_de_otro_emisor_no_es_confiable(tmp_path, certs):
    raices, _, _ = cargar_raices(carpeta_raiz(tmp_path, certs, "dos"))
    f = verificar_pdf(firmado(tmp_path, certs, "uno"), raices)["firmas"][0]
    assert f["integridad"] and f["confianza"] == "no_confiable" and f["veredicto"] == "integra"


def test_documento_alterado_es_invalido(tmp_path, certs):
    ruta = firmado(tmp_path, certs, "uno")
    datos = open(ruta, "rb").read()
    assert b"/MediaBox" in datos
    open(ruta, "wb").write(datos.replace(b"/MediaBox", b"/MediaBoy", 1))
    res = verificar_pdf(ruta)
    assert res["firmas"][0]["integridad"] is False and res["firmas"][0]["veredicto"] == "invalida"
    assert veredicto_de(res) == "invalida"


def test_cambios_posteriores_a_la_firma_se_marcan(tmp_path, certs):
    ruta = firmado(tmp_path, certs, "uno")
    doc = pymupdf.open(ruta)
    doc[0].insert_text((100, 300), "texto agregado despues", fontsize=12)
    doc.saveIncr()
    doc.close()
    f = verificar_pdf(ruta)["firmas"][0]
    assert f["cambios"] == "sospechosos" and f["veredicto"] in ("revisar", "invalida")


def test_dos_firmas_la_primera_solo_tiene_cambios_permitidos(tmp_path, certs):
    res = verificar_pdf(firmado(tmp_path, certs, "uno", "dos"))
    assert [f["campo"] for f in res["firmas"]] == ["Firma1", "Firma2"]
    assert res["firmas"][0]["cambios"] == "permitidos" and res["firmas"][1]["cambios"] == "ninguno"
    assert all(f["integridad"] for f in res["firmas"])
    assert veredicto_de(res) == "integra"


def test_certificado_vencido_al_firmar_pide_revision(tmp_path, certs):
    f = verificar_pdf(firmado(tmp_path, certs, "vencida"))["firmas"][0]
    assert f["integridad"] and f["vigente"] is False and f["veredicto"] == "revisar"


def test_pdf_sin_firmas_y_pdf_danado(tmp_path):
    sin = verificar_pdf(crear_pdf(tmp_path / "libre.pdf"))
    assert sin["firmas"] == [] and veredicto_de(sin) == "sin_firmas"
    (tmp_path / "malo.pdf").write_bytes(b"esto no es un pdf")
    malo = verificar_pdf(str(tmp_path / "malo.pdf"))
    assert veredicto_de(malo) == "error" and "dañado" in malo["error"]
    assert "Traceback" not in malo["error"] and "pdf" not in malo["error"].lower().replace("es un pdf", "")


# ------------------------------------------------------------ raíces e informe
def test_cargar_raices_ignora_archivos_ilegibles_y_otros_tipos(tmp_path, certs):
    d = carpeta_raiz(tmp_path, certs, "uno")
    (tmp_path / "raices_pem" / "roto.crt").write_bytes(b"no es un certificado")
    (tmp_path / "raices_pem" / "notas.txt").write_text("hola")
    certs_leidos, leidos, ilegibles = cargar_raices(d)
    assert (len(certs_leidos), leidos, ilegibles) == (1, 1, 1)
    assert cargar_raices("") == ([], 0, 0) and cargar_raices(str(tmp_path / "no_existe")) == ([], 0, 0)


def test_informe_csv(tmp_path, certs):
    ruta = firmado(tmp_path, certs, "uno", "dos")
    filas = aplanar([("f.pdf", verificar_pdf(ruta)),
                     ("libre.pdf", verificar_pdf(crear_pdf(tmp_path / "libre.pdf")))])
    assert [(r["archivo"], r["campo"]) for r in filas] == [("f.pdf", "Firma1"), ("f.pdf", "Firma2"),
                                                           ("libre.pdf", "")]
    salida = tmp_path / "v.csv"
    guardar_csv(str(salida), filas)
    with open(salida, encoding="utf-8-sig", newline="") as f:
        datos = list(csv.reader(f, delimiter=";"))
    assert datos[0][:3] == ["archivo", "firma", "firmante"] and len(datos) == 4
    assert datos[1][10] == "integra" and datos[3][10] == "sin_firmas"
    assert datos[1][11] == ("Después se agregó otra firma o datos de formulario. No se cargaron certificados raíz: "
                            "no se verificó quién emitió el certificado.")
    assert datos[2][11] == "No se cargaron certificados raíz: no se verificó quién emitió el certificado."


def test_mensajes_en_ingles(tmp_path, certs):
    from firmador_masivo import i18n
    ruta = firmado(tmp_path, certs, "uno")
    i18n.fijar_idioma("en")
    try:
        fila = aplanar([("f.pdf", verificar_pdf(ruta))])[0]
    finally:
        i18n.fijar_idioma("es")
    assert fila["mensaje"].startswith("No root certificates were loaded")
    assert fila["veredicto"] == "integra"          # los códigos no se traducen
