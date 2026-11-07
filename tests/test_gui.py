"""Pruebas de la ventana. Necesitan pantalla: en Linux se corren con `xvfb-run -a pytest`."""
import csv
import glob
import os
import time
import tkinter as tk
from tkinter import ttk

import pymupdf
import pytest

from conftest import CLAVE, LETTER, PIE_IZQ, crear_pdf, firmas_de

pytestmark = pytest.mark.gui

FRACCIONES = {1: (0.07, 0.88, 0.48, 0.96), 2: (0.52, 0.88, 0.93, 0.96)}


@pytest.fixture(scope="module")
def _app_modulo():
    """Una sola ventana por módulo: crear y destruir Tk muchas veces es lento y poco fiable."""
    from firmador_masivo import gui
    try:
        a = gui.App()
    except tk.TclError as e:
        if os.name != "nt" and not os.environ.get("DISPLAY"):
            pytest.skip(f"no hay pantalla disponible (usa xvfb-run): {e}")
        raise
    a.update()
    yield a
    a.destroy()


def resetear(a):
    for v in (a.p12_1, a.clave_1, a.p12_2, a.clave_2, a.carpeta_in, a.carpeta_out, a.tsa_user, a.tsa_pass):
        v.set("")
    a.usar_2.set(True); a.visible.set(True); a.qr.set(True); a.recursivo.set(False)
    a.omitir.set(True); a.evitar.set(True); a.usar_tsa.set(False)
    a.tsa_url.set("http://timestamp.digicert.com")
    a.posicion.update(modo="ultima", numero=1, cajas={}, definida=False)
    a._detener.clear(); a._continuar.set(); a._corriendo = False
    a.tiempo.set("")
    from firmador_masivo import i18n
    i18n.fijar_idioma("es")
    a._construir()          # vuelve a dibujar la ventana en español y con los botones en reposo


@pytest.fixture
def app(_app_modulo, monkeypatch):
    from firmador_masivo import gui
    resetear(_app_modulo)
    mensajes = []
    for nombre in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(gui.messagebox, nombre,
                            lambda t, m, _n=nombre, **k: mensajes.append((_n, t, m)))
    monkeypatch.setattr(gui.messagebox, "askyesno", lambda *a, **k: True)
    _app_modulo.mensajes = mensajes
    yield _app_modulo
    for w in list(_app_modulo.winfo_children()):
        if isinstance(w, tk.Toplevel):
            w.destroy()


def esperar(app, condicion, timeout=60):
    """Corre el mainloop real (el hilo de trabajo lo necesita) hasta que 'condicion' sea cierta.
    La condición se evalúa dentro del mainloop, así puede ejecutar acciones (pausar, detener...)."""
    fin = time.time() + timeout
    res = {"ok": False}

    def vigilar():
        if condicion():
            res["ok"] = True
            app.quit()
        elif time.time() > fin:
            app.quit()
        else:
            app.after(20, vigilar)
    app.after(20, vigilar)
    app.mainloop()
    return res["ok"]


def preparar(app, certs, entrada, salida, recursivo=True):
    app.p12_1.set(certs["uno"]); app.clave_1.set(CLAVE)
    app.p12_2.set(certs["dos"]); app.clave_2.set(CLAVE)
    app.carpeta_in.set(str(entrada)); app.carpeta_out.set(str(salida))
    app.recursivo.set(recursivo)
    app._guardar_posicion("ultima", 1, dict(FRACCIONES))


def corrida(app):
    app.mensajes.clear()
    app._iniciar()
    assert esperar(app, lambda: any(m[1] in ("Listo", "Terminado con avisos", "Proceso detenido", "Sin PDFs")
                                    or m[0] == "showerror" or m[1].startswith("Falta")
                                    for m in app.mensajes))
    return app.mensajes[-1]


def textos_de_widgets(w):
    out = []
    for hijo in w.winfo_children():
        for opcion in ("text",):
            try:
                t = hijo.cget(opcion)
                if t:
                    out.append(str(t))
            except tk.TclError:
                pass
        out.extend(textos_de_widgets(hijo))
    return out


# ------------------------------------------------------------------ texto
def test_ortografia_de_la_interfaz(app):
    todo = " ".join(textos_de_widgets(app))
    for bien in ("Contraseña", "Elegir posición", "código QR", "ya están", "Firma 1"):
        assert bien in todo, bien
    for mal in ("Contrasena", "posicion", "codigo", "ya estan", "electronica"):
        assert mal not in todo, mal
    assert app.texto_pos.get() == "Posición: sin definir"


def test_valores_por_defecto(app):
    assert app.tsa_url.get() == "http://timestamp.digicert.com"
    assert app.usar_tsa.get() is False
    assert app.evitar.get() is True and app.omitir.get() is True and app.qr.get() is True
    assert app.usar_2.get() is True


# --------------------------------------------------------------- validación
def test_validar_firmas(app, certs):
    app.p12_1.set(certs["uno"]); app.clave_1.set(CLAVE)
    app.p12_2.set(certs["vencida"]); app.clave_2.set(CLAVE)
    assert app._validar() is False
    assert app.mensajes[-1][1] == "Revisa las firmas" and "VENCIDA" in app.mensajes[-1][2]
    app.p12_2.set(certs["dos"])
    assert app._validar() is True
    assert app.mensajes[-1][1] == "Firmas correctas"


def test_iniciar_pide_posicion_y_datos(app, certs, tmp_path):
    app._iniciar()
    assert app.mensajes[-1][1] == "Falta información"
    app.p12_1.set(certs["uno"]); app.clave_1.set(CLAVE)
    app.p12_2.set(certs["dos"]); app.clave_2.set(CLAVE)
    entrada = tmp_path / "in"; entrada.mkdir()
    app.carpeta_in.set(str(entrada)); app.carpeta_out.set(str(tmp_path / "out"))
    app._iniciar()
    assert app.mensajes[-1][1] == "Falta la posición"
    app.carpeta_out.set(str(entrada))
    app._guardar_posicion("ultima", 1, dict(FRACCIONES))
    app._iniciar()
    assert app.mensajes[-1][1] == "Carpetas iguales"


def test_tsa_sin_url_avisa(app, certs, tmp_path):
    entrada = tmp_path / "in"; entrada.mkdir()
    preparar(app, certs, entrada, tmp_path / "out")
    app.usar_tsa.set(True); app.tsa_url.set("")
    app._iniciar()
    assert app.mensajes[-1][1] == "Falta el servidor de sello de tiempo"


# ------------------------------------------------------------ selector
def test_selector_dibujar_y_aceptar(app, tmp_path):
    from firmador_masivo.gui import SelectorPosicion
    crear_pdf(tmp_path / "ej.pdf")
    app.carpeta_in.set(str(tmp_path)); app.carpeta_out.set(str(tmp_path / "out"))
    app._abrir_selector(); app.update()
    sel = [w for w in app.winfo_children() if isinstance(w, SelectorPosicion)][0]
    cv = sel.canvas

    def arrastrar(x0, y0, x1, y1):
        cv.event_generate("<ButtonPress-1>", x=x0, y=y0)
        cv.event_generate("<B1-Motion>", x=(x0 + x1) // 2, y=(y0 + y1) // 2)
        cv.event_generate("<B1-Motion>", x=x1, y=y1)
        cv.event_generate("<ButtonRelease-1>", x=x1, y=y1)
        sel.update()

    arrastrar(40, int(sel.h * .80), int(sel.w * .48), int(sel.h * .92))
    assert sel.activa.get() == 2            # pasa sola a la segunda firma
    arrastrar(int(sel.w * .52), int(sel.h * .80), int(sel.w * .93), int(sel.h * .92))
    sel._aceptar(); app.update()
    assert app.texto_pos.get() == "Posición definida (última página)"
    assert set(app.posicion["cajas"]) == {1, 2} and app.posicion["definida"]


def test_selector_con_pdf_danado_da_mensaje_claro(app, tmp_path):
    (tmp_path / "malo.pdf").write_bytes(b"esto no es un pdf")
    app.carpeta_in.set(str(tmp_path)); app.carpeta_out.set(str(tmp_path / "out"))
    app._abrir_selector()
    tipo, titulo, texto = app.mensajes[-1]
    assert titulo == "No se pudo abrir el PDF"
    assert "dañado" in texto and "Failed to open" not in texto


# -------------------------------------------------------------- corrida
def test_corrida_completa_con_pdf_danado_y_reanudacion(app, certs, tmp_path):
    entrada, salida = tmp_path / "in", tmp_path / "out"
    (entrada / "A001 Factura").mkdir(parents=True)
    crear_pdf(entrada / "A001 Factura" / "uno.pdf", tam=LETTER, textos=PIE_IZQ)
    (entrada / "B" / "C").mkdir(parents=True)
    crear_pdf(entrada / "B" / "C" / "dos.pdf")
    (entrada / "A001 Factura" / "dañado.pdf").write_bytes(b"esto no es un pdf")
    preparar(app, certs, entrada, salida)

    assert corrida(app)[1] == "Terminado con avisos"
    assert sorted(os.path.relpath(f, salida) for f in glob.glob(str(salida / "**" / "*.pdf"), recursive=True)) == \
        [os.path.join("A001 Factura", "uno.pdf"), os.path.join("B", "C", "dos.pdf")]
    for f in glob.glob(str(salida / "**" / "*.pdf"), recursive=True):
        assert firmas_de(f) == [("Firma1", True), ("Firma2", True)]
    # los originales quedan intactos
    assert firmas_de(str(entrada / "B" / "C" / "dos.pdf")) == []

    errores = (salida / "errores_firmado.txt").read_text(encoding="utf-8")
    assert "dañado.pdf: El archivo está dañado o no es un PDF válido." in errores
    assert "Failed to open" not in errores

    csv_ruta = glob.glob(str(salida / "registro_firmado_*.csv"))[0]
    with open(csv_ruta, encoding="utf-8-sig", newline="") as f:
        filas = {r[2]: r for r in csv.reader(f, delimiter=";")}
    assert filas["dañado.pdf"][3] == "error" and "dañado" in filas["dañado.pdf"][8]
    assert filas["uno.pdf"][3] == "firmado" and filas["uno.pdf"][4] == "ajustada"
    assert glob.glob(str(salida / "resumen_firmado_*.txt"))

    # segunda corrida: omite lo ya firmado
    corrida(app)
    with open(sorted(glob.glob(str(salida / "registro_firmado_*.csv")))[-1], encoding="utf-8-sig", newline="") as f:
        estados = {r[2]: r[3] for r in csv.reader(f, delimiter=";")}
    assert estados["uno.pdf"] == "omitido" and estados["dos.pdf"] == "omitido"


def test_corrida_sin_firma_visible(app, certs, tmp_path):
    entrada, salida = tmp_path / "in", tmp_path / "out"
    crear_pdf(entrada / "a.pdf")
    preparar(app, certs, entrada, salida, recursivo=False)
    app.visible.set(False)
    assert corrida(app)[1] == "Listo"
    assert firmas_de(str(salida / "a.pdf")) == [("Firma1", True), ("Firma2", True)]
    assert "Firmado" not in pymupdf.open(str(salida / "a.pdf"))[0].get_text()


def test_sin_espacio_no_firma_y_lo_informa(app, certs, tmp_path):
    from conftest import LLENO
    entrada, salida = tmp_path / "in", tmp_path / "out"
    crear_pdf(entrada / "lleno.pdf", textos=LLENO(792))
    crear_pdf(entrada / "libre.pdf")
    preparar(app, certs, entrada, salida, recursivo=False)
    assert corrida(app)[1] == "Terminado con avisos"
    assert not (salida / "lleno.pdf").exists() and (salida / "libre.pdf").exists()
    with open(glob.glob(str(salida / "registro_firmado_*.csv"))[0], encoding="utf-8-sig", newline="") as f:
        filas = {r[2]: r for r in csv.reader(f, delimiter=";")}
    assert filas["lleno.pdf"][3] == "sin_espacio"
    assert filas["lleno.pdf"][8] == "No hay espacio libre para las firmas en la página 1"


def test_carpeta_vacia(app, certs, tmp_path):
    entrada = tmp_path / "in"; entrada.mkdir()
    preparar(app, certs, entrada, tmp_path / "out")
    assert corrida(app)[1] == "Sin PDFs"


def _lote(tmp_path, n):
    entrada = tmp_path / "in"
    entrada.mkdir()
    datos = open(crear_pdf(tmp_path / "base.pdf"), "rb").read()
    for i in range(n):
        (entrada / f"d{i:03d}.pdf").write_bytes(datos)
    return entrada


def _cuenta(salida):
    return len(glob.glob(str(salida / "*.pdf")))


def test_detener_y_continuar(app, certs, tmp_path):
    entrada, salida = _lote(tmp_path, 40), tmp_path / "out"
    preparar(app, certs, entrada, salida, recursivo=False)
    app.qr.set(False)
    app.mensajes.clear()
    app._iniciar()
    paro = {"hecho": False}

    def cond():
        if not paro["hecho"] and _cuenta(salida) >= 2:
            app._parar()
            paro["hecho"] = True
        return paro["hecho"] and any(m[1] == "Proceso detenido" for m in app.mensajes)
    assert esperar(app, cond)
    assert 0 < _cuenta(salida) < 40
    assert str(app.btn.cget("state")) == "normal"
    assert corrida(app)[1] == "Listo"          # continúa donde quedó
    assert _cuenta(salida) == 40


def test_pausar_y_reanudar(app, certs, tmp_path):
    entrada, salida = _lote(tmp_path, 30), tmp_path / "out"
    preparar(app, certs, entrada, salida, recursivo=False)
    app.qr.set(False)
    app.mensajes.clear()
    app._iniciar()
    est = {"fase": 0, "t": 0.0, "n": 0}

    def cond():
        if est["fase"] == 0 and _cuenta(salida) >= 2:
            app._pausar()
            est.update(fase=1, t=time.time())
        elif est["fase"] == 1 and time.time() - est["t"] > 1.0:     # deja terminar el archivo en curso
            est.update(fase=2, t=time.time(), n=_cuenta(salida))
        elif est["fase"] == 2 and time.time() - est["t"] > 1.0:
            assert _cuenta(salida) == est["n"], "en pausa no debe avanzar"
            assert str(app.btn_reanuda.cget("state")) == "normal"
            assert str(app.btn_pausa.cget("state")) == "disabled"
            app._reanudar()
            est["fase"] = 3
        return est["fase"] == 3 and any(m[1] == "Listo" for m in app.mensajes)
    assert esperar(app, cond)
    assert _cuenta(salida) == 30


# ------------------------------------------------------------------ idioma
@pytest.mark.parametrize("cod,boton,contrasena,posicion", [
    ("en", "SIGN DOCUMENTS", "Password:", "Position: not set"),
    ("pt", "ASSINAR DOCUMENTOS", "Senha:", "Posição: não definida"),
    ("es", "FIRMAR DOCUMENTOS", "Contraseña:", "Posición: sin definir"),
])
def test_cambiar_idioma_redibuja_la_ventana(app, cod, boton, contrasena, posicion):
    from firmador_masivo import i18n
    app.p12_1.set("conservado.p12")                      # lo escrito no se pierde al cambiar
    app.idioma_nombre.set(i18n.IDIOMAS[cod])
    if cod == "es":                                      # parte de otro idioma para que haya cambio
        i18n.fijar_idioma("en"); app._construir(); app.idioma_nombre.set(i18n.IDIOMAS["es"])
    app._cambiar_idioma()
    textos = textos_de_widgets(app)
    assert boton in textos and contrasena in textos
    assert app.texto_pos.get() == posicion
    assert app.p12_1.get() == "conservado.p12"
    assert i18n.idioma_actual() == cod


def test_idioma_se_recuerda(app):
    from firmador_masivo import i18n
    app.idioma_nombre.set(i18n.IDIOMAS["pt"])
    app._cambiar_idioma()
    i18n.fijar_idioma("es")
    assert i18n.iniciar() == "pt"


def test_no_se_cambia_idioma_mientras_se_firma(app):
    from firmador_masivo import i18n
    app._corriendo = True
    app.idioma_nombre.set(i18n.IDIOMAS["en"])
    app._cambiar_idioma()
    assert i18n.idioma_actual() == "es" and app.idioma_nombre.get() == i18n.IDIOMAS["es"]
    app._corriendo = False


def test_corrida_en_ingles(app, certs, tmp_path):
    from firmador_masivo import i18n
    entrada, salida = tmp_path / "in", tmp_path / "out"
    crear_pdf(entrada / "a.pdf")
    (entrada / "malo.pdf").write_bytes(b"esto no es un pdf")
    preparar(app, certs, entrada, salida, recursivo=False)
    i18n.fijar_idioma("en"); app._construir()
    assert corrida(app)[1] == "Finished with warnings"
    assert "The file is damaged or is not a valid PDF." in (salida / "errores_firmado.txt").read_text(encoding="utf-8")
    texto = pymupdf.open(str(salida / "a.pdf"))[-1].get_text()
    assert "Electronically signed by" in texto and "Firmado" not in texto
    resumen = glob.glob(str(salida / "resumen_firmado_*.txt"))[0]
    assert "MASS SIGNING REPORT" in open(resumen, encoding="utf-8").read()
