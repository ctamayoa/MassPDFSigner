"""Interfaz gráfica (Tkinter). El trabajo pesado corre en un hilo aparte."""
import os
import socket
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import i18n
from .archivos import listar_pdfs, ruta_larga
from .errores import describir_error
from .firmas import (cargar_firmante, crear_sellador, firmar_un_pdf, nombre_titular,
                     probar_sellador, revisar_firma)
from .i18n import IDIOMAS, t
from .informes import fmt_fecha, fmt_hms, guardar_informes, resumen_corto
from .posicion import COLORES, DEFECTO, SinEspacio, cajas_para_pdf, fitz, indice_pagina


# ------------------------------------------------- ventana de posición ---
class SelectorPosicion(tk.Toplevel):
    """Muestra un PDF y deja dibujar con el mouse el recuadro de cada firma."""

    def __init__(self, master, ruta_pdf, usar_2, estado, al_aceptar):
        super().__init__(master)
        self.title(t("sel.titulo"))
        self.transient(master)
        self.grab_set()
        self.doc = fitz.open(ruta_pdf)
        self.usar_2 = usar_2
        self.al_aceptar = al_aceptar
        self.cajas = {k: v for k, v in estado["cajas"].items() if k == 1 or usar_2}
        self.modo = tk.StringVar(value=estado["modo"])
        self.numero = tk.IntVar(value=estado["numero"])
        self.activa = tk.IntVar(value=1)
        self.inicio = None
        self.foto = None
        self.dibujadas = set()

        barra = ttk.Frame(self)
        barra.pack(fill="x", padx=8, pady=6)
        ttk.Label(barra, text=t("sel.pagina")).pack(side="left")
        for texto, valor in ((t("sel.primera"), "primera"), (t("sel.ultima"), "ultima"), (t("sel.numero"), "numero")):
            ttk.Radiobutton(barra, text=texto, value=valor, variable=self.modo,
                            command=self._redibujar).pack(side="left", padx=3)
        self.spin = ttk.Spinbox(barra, from_=1, to=self.doc.page_count, width=4,
                                textvariable=self.numero, command=self._redibujar)
        self.spin.pack(side="left")
        self.spin.bind("<Return>", lambda e: self._redibujar())

        ttk.Separator(barra, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Label(barra, text=t("sel.dibujar")).pack(side="left")
        ttk.Radiobutton(barra, text=t("sel.firma1"), value=1, variable=self.activa).pack(side="left", padx=3)
        if usar_2:
            ttk.Radiobutton(barra, text=t("sel.firma2"), value=2, variable=self.activa).pack(side="left", padx=3)

        ttk.Label(self, text=t("sel.ayuda")).pack(anchor="w", padx=8)

        pie = ttk.Frame(self)
        pie.pack(side="bottom", fill="x", padx=8, pady=8)
        ttk.Button(pie, text=t("sel.cancelar"), command=self.destroy).pack(side="right", padx=4)
        ttk.Button(pie, text=t("sel.aceptar"), command=self._aceptar).pack(side="right", padx=4)

        self.canvas = tk.Canvas(self, bg="#888", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="top", padx=8, pady=6)
        self.canvas.bind("<ButtonPress-1>", self._presionar)
        self.canvas.bind("<B1-Motion>", self._arrastrar)
        self.canvas.bind("<ButtonRelease-1>", self._soltar)

        self._redibujar()
        self.update_idletasks()
        x = max(0, (self.winfo_screenwidth() - self.winfo_width()) // 2)
        self.geometry(f"+{x}+10")

    # --- dibujo
    def _indice(self):
        try:
            n = int(self.numero.get())
        except (tk.TclError, ValueError):
            n = 1
        return indice_pagina(self.doc.page_count, self.modo.get(), n)

    def _redibujar(self):
        page = self.doc[self._indice()]
        alto_max = max(300, self.winfo_screenheight() - 300)   # barra de título, botones, barra de tareas
        ancho_max = max(300, min(620, self.winfo_screenwidth() - 100))
        zoom = min(ancho_max / page.rect.width, alto_max / page.rect.height)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        self.foto = tk.PhotoImage(data=pix.tobytes("png"))
        self.w, self.h = pix.width, pix.height
        self.canvas.config(width=self.w, height=self.h)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.foto)
        for n, (a, b, c, d) in self.cajas.items():
            self._rect(n, a * self.w, b * self.h, c * self.w, d * self.h)

    def _rect(self, n, x0, y0, x1, y1):
        self.canvas.delete(f"r{n}")
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=COLORES[n], width=2,
                                     fill=COLORES[n], stipple="gray25", tags=f"r{n}")
        self.canvas.create_text(x0 + 4, y0 + 4, anchor="nw", text=t("sel.etiqueta", n=n),
                                fill=COLORES[n], font=("Segoe UI", 9, "bold"), tags=f"r{n}")

    # --- mouse
    def _limitar(self, e):
        return min(max(e.x, 0), self.w), min(max(e.y, 0), self.h)

    def _presionar(self, e):
        self.inicio = self._limitar(e)

    def _arrastrar(self, e):
        if not self.inicio:
            return
        x, y = self._limitar(e)
        self._rect(self.activa.get(), self.inicio[0], self.inicio[1], x, y)

    def _soltar(self, e):
        if not self.inicio:
            return
        x, y = self._limitar(e)
        x0, x1 = sorted((self.inicio[0], x))
        y0, y1 = sorted((self.inicio[1], y))
        self.inicio = None
        if x1 - x0 < 20 or y1 - y0 < 15:  # clic suelto o recuadro diminuto
            self._redibujar()
            return
        n = self.activa.get()
        self.cajas[n] = (x0 / self.w, y0 / self.h, x1 / self.w, y1 / self.h)
        self._rect(n, x0, y0, x1, y1)
        self.dibujadas.add(n)
        if n == 1 and self.usar_2 and 2 not in self.dibujadas:
            self.activa.set(2)

    def _aceptar(self):
        faltan = [n for n in ((1, 2) if self.usar_2 else (1,)) if n not in self.cajas]
        if faltan:
            messagebox.showwarning(t("sel.falta_titulo"), t("sel.falta_texto", n=faltan[0]), parent=self)
            return
        try:
            numero = int(self.numero.get())
        except (tk.TclError, ValueError):
            numero = 1
        self.al_aceptar(self.modo.get(), numero, dict(self.cajas))
        self.destroy()

    def destroy(self):
        try:
            self.doc.close()
        except Exception:
            pass
        super().destroy()


# ------------------------------------------------------------------- GUI ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        i18n.iniciar()
        self.resizable(False, False)
        self.columnconfigure(1, weight=1)

        # Las variables viven aquí para conservar lo escrito cuando se cambia de idioma
        self.p12_1 = tk.StringVar()
        self.clave_1 = tk.StringVar()
        self.p12_2 = tk.StringVar()
        self.clave_2 = tk.StringVar()
        self.usar_2 = tk.BooleanVar(value=True)
        self.carpeta_in = tk.StringVar()
        self.carpeta_out = tk.StringVar()
        self.visible = tk.BooleanVar(value=True)
        self.qr = tk.BooleanVar(value=True)
        self._continuar = threading.Event()
        self._continuar.set()
        self._detener = threading.Event()
        self.recursivo = tk.BooleanVar(value=False)
        self.omitir = tk.BooleanVar(value=True)
        self.evitar = tk.BooleanVar(value=True)
        self.usar_tsa = tk.BooleanVar(value=False)
        self.tsa_url = tk.StringVar(value="http://timestamp.digicert.com")
        self.tsa_user = tk.StringVar()
        self.tsa_pass = tk.StringVar()
        self.posicion = {"modo": "ultima", "numero": 1, "cajas": {}, "definida": False}
        self.texto_pos = tk.StringVar()
        self.tiempo = tk.StringVar(value="")
        self.estado = tk.StringVar()
        self.idioma_nombre = tk.StringVar()
        self._corriendo = False
        self._pausa_ini = None
        self._pausa_total = 0.0

        self._construir()

    # ------------------------------------------------------------- ventana
    def _construir(self):
        """Dibuja toda la ventana con los textos del idioma actual."""
        for w in self.winfo_children():
            if not isinstance(w, tk.Toplevel):
                w.destroy()
        self.title(t("app.titulo"))
        self._actualizar_texto_pos()
        self.estado.set(t("estado.listo"))
        self.idioma_nombre.set(IDIOMAS[i18n.idioma_actual()])

        pad = {"padx": 8, "pady": 4}
        fila = 0

        barra_idioma = ttk.Frame(self)
        barra_idioma.grid(row=fila, column=0, columnspan=3, sticky="e", padx=8, pady=(4, 0))
        ttk.Label(barra_idioma, text=t("ui.idioma")).pack(side="left", padx=(0, 4))
        self.combo_idioma = ttk.Combobox(barra_idioma, textvariable=self.idioma_nombre, state="readonly",
                                         width=11, values=list(IDIOMAS.values()))
        self.combo_idioma.pack(side="left")
        self.combo_idioma.bind("<<ComboboxSelected>>", lambda e: self.after(0, self._cambiar_idioma))
        fila += 1

        f1 = ttk.LabelFrame(self, text=t("ui.firma1"))
        f1.grid(row=fila, column=0, columnspan=3, sticky="ew", **pad)
        self._bloque_firma(f1, self.p12_1, self.clave_1)
        fila += 1

        f2 = ttk.LabelFrame(self, text=t("ui.firma2"))
        f2.grid(row=fila, column=0, columnspan=3, sticky="ew", **pad)
        ttk.Checkbutton(
            f2, text=t("ui.usar_2"), variable=self.usar_2,
            command=self._alternar_firma2,
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=6)
        self._bloque_firma(f2, self.p12_2, self.clave_2, fila_inicio=1)
        self.f2 = f2
        self._aplicar_estado_firma2()
        fila += 1

        ttk.Label(self, text=t("ui.carpeta_pdfs")).grid(row=fila, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.carpeta_in, width=50).grid(row=fila, column=1, **pad)
        ttk.Button(self, text=t("ui.elegir"), command=lambda: self._carpeta(self.carpeta_in)).grid(row=fila, column=2, **pad)
        fila += 1
        ttk.Label(self, text=t("ui.carpeta_salida")).grid(row=fila, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.carpeta_out, width=50).grid(row=fila, column=1, **pad)
        ttk.Button(self, text=t("ui.elegir"), command=lambda: self._carpeta(self.carpeta_out)).grid(row=fila, column=2, **pad)
        fila += 1

        sub = ttk.Frame(self)
        sub.grid(row=fila, column=0, columnspan=3, sticky="w", **pad)
        ttk.Checkbutton(sub, text=t("ui.subcarpetas"), variable=self.recursivo).pack(anchor="w")
        ttk.Checkbutton(sub, text=t("ui.omitir"), variable=self.omitir).pack(anchor="w")
        ttk.Checkbutton(sub, text=t("ui.evitar"), variable=self.evitar).pack(anchor="w")
        fila += 1

        op = ttk.Frame(self)
        op.grid(row=fila, column=0, columnspan=3, sticky="w", **pad)
        ttk.Checkbutton(op, text=t("ui.visible"), variable=self.visible).pack(side="left")
        self.btn_pos = ttk.Button(op, text=t("ui.elegir_pos"), command=self._abrir_selector)
        self.btn_pos.pack(side="left", padx=12)
        ttk.Label(op, textvariable=self.texto_pos).pack(side="left")
        fila += 1

        ttk.Checkbutton(self, text=t("ui.qr"), variable=self.qr).grid(
            row=fila, column=0, columnspan=3, sticky="w", padx=8, pady=2)
        fila += 1

        ft = ttk.LabelFrame(self, text=t("ui.tsa_marco"))
        ft.grid(row=fila, column=0, columnspan=3, sticky="ew", **pad)
        ttk.Checkbutton(ft, text=t("ui.tsa_usar"), variable=self.usar_tsa,
                        command=self._alternar_tsa).grid(row=0, column=0, columnspan=4, sticky="w", padx=6)
        ttk.Label(ft, text=t("ui.tsa_url")).grid(row=1, column=0, sticky="w", padx=6, pady=3)
        self.e_tsa_url = ttk.Entry(ft, textvariable=self.tsa_url, width=52)
        self.e_tsa_url.grid(row=1, column=1, columnspan=2, sticky="w", padx=6)
        self.btn_tsa = ttk.Button(ft, text=t("ui.tsa_probar"), command=self._probar_tsa)
        self.btn_tsa.grid(row=1, column=3, padx=6)
        ttk.Label(ft, text=t("ui.tsa_usuario")).grid(row=2, column=0, sticky="w", padx=6, pady=3)
        self.e_tsa_user = ttk.Entry(ft, textvariable=self.tsa_user, width=22)
        self.e_tsa_user.grid(row=2, column=1, sticky="w", padx=6)
        ttk.Label(ft, text=t("ui.tsa_clave")).grid(row=2, column=2, sticky="e")
        self.e_tsa_pass = ttk.Entry(ft, textvariable=self.tsa_pass, show="*", width=18)
        self.e_tsa_pass.grid(row=2, column=3, sticky="w", padx=6)
        ttk.Label(
            ft, text=t("ui.tsa_aviso"),
            foreground="#555555", wraplength=640, justify="left",
        ).grid(row=3, column=0, columnspan=4, sticky="w", padx=6, pady=(2, 4))
        self._alternar_tsa()
        fila += 1

        botones = ttk.Frame(self)
        botones.grid(row=fila, column=0, columnspan=3, sticky="ew", padx=8, pady=8)
        botones.columnconfigure(1, weight=1)
        self.btn_val = ttk.Button(botones, text=t("ui.validar"), command=self._validar)
        self.btn_val.grid(row=0, column=0, sticky="ns", padx=(0, 8), ipadx=10)
        self.btn = ttk.Button(botones, text=t("ui.firmar"), command=self._iniciar)
        self.btn.grid(row=0, column=1, sticky="ew", ipady=8)
        fila += 1
        self._crear_iconos()
        control = ttk.Frame(self)
        control.grid(row=fila, column=0, columnspan=3, sticky="ew", padx=8, pady=2)
        for c in range(3):
            control.columnconfigure(c, weight=1)
        self.btn_pausa = ttk.Button(control, text=t("ui.pausar"), command=self._pausar, state="disabled",
                                    image=self._iconos["pausa_off"], compound="left")
        self.btn_pausa.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=3)
        self.btn_reanuda = ttk.Button(control, text=t("ui.reanudar"), command=self._reanudar, state="disabled",
                                      image=self._iconos["reanuda_off"], compound="left")
        self.btn_reanuda.grid(row=0, column=1, sticky="ew", padx=4, ipady=3)
        self.btn_parar = ttk.Button(control, text=t("ui.detener"), command=self._parar, state="disabled",
                                    image=self._iconos["parar_off"], compound="left")
        self.btn_parar.grid(row=0, column=2, sticky="ew", padx=(4, 0), ipady=3)
        fila += 1
        self.barra = ttk.Progressbar(self, length=400, mode="determinate")
        self.barra.grid(row=fila, column=0, columnspan=3, sticky="ew", **pad)
        fila += 1
        ttk.Label(self, textvariable=self.estado).grid(row=fila, column=0, columnspan=3, sticky="w", **pad)
        fila += 1
        ttk.Label(self, textvariable=self.tiempo, foreground="#444444").grid(
            row=fila, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 6))

    def _cambiar_idioma(self):
        nombre = self.idioma_nombre.get()
        cod = next((c for c, n in IDIOMAS.items() if n == nombre), i18n.idioma_actual())
        if self._corriendo:  # no se redibuja la ventana mientras se firma
            self.idioma_nombre.set(IDIOMAS[i18n.idioma_actual()])
            return
        if cod == i18n.idioma_actual():
            return
        i18n.fijar_idioma(cod)
        i18n.guardar_preferencia(cod)
        self._construir()

    @staticmethod
    def _dibujar_icono(forma, color, tam=16):
        """Ícono pequeño dibujado píxel a píxel (sin archivos ni librerías extra)."""
        img = tk.PhotoImage(width=tam, height=tam)
        if forma == "pausa":
            for x0 in (3, 9):
                img.put(color, to=(x0, 2, x0 + 4, tam - 2))
        elif forma == "reanuda":
            for y in range(2, tam - 2):
                ancho = int((6 - abs(y - 7.5)) * 2.0)
                if ancho > 0:
                    img.put(color, to=(3, y, 3 + ancho, y + 1))
        else:  # parar
            img.put(color, to=(3, 3, tam - 3, tam - 3))
        return img

    def _crear_iconos(self):
        colores = {"pausa": "#e08a00", "reanuda": "#1f9d3a", "parar": "#d62828"}
        self._iconos = {}
        for nombre, color in colores.items():
            self._iconos[nombre] = self._dibujar_icono(nombre, color)
            self._iconos[nombre + "_off"] = self._dibujar_icono(nombre, "#b0b0b0")

    def _fijar(self, boton, nombre, activo):
        boton.configure(state="normal" if activo else "disabled",
                        image=self._iconos[nombre if activo else nombre + "_off"])

    def _bloque_firma(self, padre, var_p12, var_clave, fila_inicio=0):
        ttk.Label(padre, text=t("ui.p12")).grid(row=fila_inicio, column=0, sticky="w", padx=6, pady=3)
        ttk.Entry(padre, textvariable=var_p12, width=48).grid(row=fila_inicio, column=1, padx=6)
        ttk.Button(padre, text=t("ui.buscar"), command=lambda: self._archivo(var_p12)).grid(
            row=fila_inicio, column=2, padx=6)
        ttk.Label(padre, text=t("ui.contrasena")).grid(row=fila_inicio + 1, column=0, sticky="w", padx=6, pady=3)
        ttk.Entry(padre, textvariable=var_clave, show="*", width=30).grid(
            row=fila_inicio + 1, column=1, sticky="w", padx=6)

    def _aplicar_estado_firma2(self):
        estado = "normal" if self.usar_2.get() else "disabled"
        for w in self.f2.winfo_children():
            if isinstance(w, (ttk.Entry, ttk.Button)):
                w.configure(state=estado)

    def _alternar_firma2(self):
        self._aplicar_estado_firma2()
        # al cambiar de 1 a 2 firmas hay que volver a definir la posición
        self.posicion["definida"] = False
        self._actualizar_texto_pos()

    def _archivo(self, var):
        r = filedialog.askopenfilename(
            title=t("dlg.p12_titulo"),
            filetypes=[(t("dlg.p12_tipo"), "*.p12 *.pfx"), (t("dlg.todos"), "*.*")])
        if r:
            var.set(r)

    def _carpeta(self, var):
        r = filedialog.askdirectory()
        if r:
            var.set(r)

    def _alternar_tsa(self):
        estado = "normal" if self.usar_tsa.get() else "disabled"
        for w in (self.e_tsa_url, self.btn_tsa, self.e_tsa_user, self.e_tsa_pass):
            w.configure(state=estado)

    def _probar_tsa(self):
        url, user, clave = self.tsa_url.get(), self.tsa_user.get(), self.tsa_pass.get()
        self.btn_tsa.configure(state="disabled")
        self.estado.set(t("estado.probando_tsa"))

        def trabajo():
            ok, texto = probar_sellador(url, user, clave)

            def mostrar():
                self.btn_tsa.configure(state="normal")
                self.estado.set(t("estado.listo"))
                (messagebox.showinfo if ok else messagebox.showwarning)(t("tsa.titulo"), texto)
            self.after(0, mostrar)
        threading.Thread(target=trabajo, daemon=True).start()

    def _validar(self):
        pares = [(t("ui.firma1"), self.p12_1.get(), self.clave_1.get())]
        if self.usar_2.get():
            pares.append((t("ui.firma2"), self.p12_2.get(), self.clave_2.get()))
        lineas, todo_ok = [], True
        for etiqueta, ruta, clave in pares:
            ok, texto = revisar_firma(ruta, clave)
            todo_ok &= ok
            lineas.append((t("val.etq_ok") if ok else t("val.etq_error")) + etiqueta + ":\n" + texto)
        mensaje = "\n\n".join(lineas)
        if todo_ok:
            messagebox.showinfo(t("val.ok_titulo"), mensaje)
        else:
            messagebox.showwarning(t("val.revisar_titulo"), mensaje)
        return todo_ok

    def _lista_pdfs(self):
        return listar_pdfs(self.carpeta_in.get(), self.carpeta_out.get(), self.recursivo.get())

    # ------------------------------------------------------------ posición
    def _abrir_selector(self):
        pdfs = self._lista_pdfs()
        if not pdfs:
            messagebox.showwarning(t("msg.primero_carpeta_t"), t("msg.primero_carpeta"))
            return
        ruta = os.path.join(self.carpeta_in.get(), pdfs[0])
        cajas = self.posicion["cajas"] or dict(DEFECTO)
        estado = {"modo": self.posicion["modo"], "numero": self.posicion["numero"], "cajas": cajas}
        try:
            SelectorPosicion(self, ruta, self.usar_2.get(), estado, self._guardar_posicion)
        except Exception as e:
            messagebox.showerror(t("msg.no_abrir_pdf"), f"{os.path.basename(pdfs[0])}\n\n{describir_error(e)}")

    def _guardar_posicion(self, modo, numero, cajas):
        self.posicion.update(modo=modo, numero=numero, cajas=cajas, definida=True)
        self._actualizar_texto_pos()

    def _actualizar_texto_pos(self):
        if not self.posicion["definida"]:
            self.texto_pos.set(t("pos.sin_definir"))
            return
        modo, numero = self.posicion["modo"], self.posicion["numero"]
        donde = {"primera": t("pos.primera"), "ultima": t("pos.ultima")}.get(modo, t("pos.pagina", n=numero))
        self.texto_pos.set(t("pos.definida", donde=donde))

    # ------------------------------------------------------------- control
    def _estado_botones(self, corriendo, pausado=False):
        self.btn.configure(state="disabled" if corriendo else "normal")
        self._fijar(self.btn_pausa, "pausa", corriendo and not pausado)
        self._fijar(self.btn_reanuda, "reanuda", corriendo and pausado)
        self._fijar(self.btn_parar, "parar", corriendo)

    def _cerrar_pausa(self):
        if self._pausa_ini is not None:
            self._pausa_total += time.time() - self._pausa_ini
            self._pausa_ini = None

    def _tick(self):
        if not self._corriendo:
            return
        ahora = time.time()
        en_pausa = (ahora - self._pausa_ini) if self._pausa_ini is not None else 0.0
        activo = ahora - self._t0 - self._pausa_total - en_pausa
        pend = self._total - self._hechos
        txt = t("tiempo.transcurrido", t=fmt_hms(activo))
        if self._n_firmados > 0 and pend > 0:
            prom = self._suma_firmados / self._n_firmados
            txt += t("tiempo.restante", t=fmt_hms(prom * pend), prom=prom)
        if self._pausa_ini is not None:
            txt += t("tiempo.en_pausa")
        self.tiempo.set(txt)
        self.after(1000, self._tick)

    def _pausar(self):
        self._pausa_ini = time.time()
        self._continuar.clear()
        self._estado_botones(True, pausado=True)
        self.estado.set(t("estado.pausando"))

    def _reanudar(self):
        self._cerrar_pausa()
        self._continuar.set()
        self._estado_botones(True, pausado=False)

    def _parar(self):
        if not messagebox.askyesno(t("parar.titulo"), t("parar.texto")):
            return
        self._detener.set()
        self._cerrar_pausa()
        self._continuar.set()  # libera la espera si estaba en pausa
        self._estado_botones(True)
        self._fijar(self.btn_pausa, "pausa", False)
        self._fijar(self.btn_parar, "parar", False)
        self.estado.set(t("estado.deteniendo"))

    # ------------------------------------------------------------- proceso
    def _iniciar(self):
        if not self.p12_1.get() or not self.clave_1.get():
            messagebox.showwarning(t("init.falta_t"), t("init.firma1"))
            return
        if self.usar_2.get() and (not self.p12_2.get() or not self.clave_2.get()):
            messagebox.showwarning(t("init.falta_t"), t("init.firma2"))
            return
        if not os.path.isdir(self.carpeta_in.get()) or not self.carpeta_out.get():
            messagebox.showwarning(t("init.falta_t"), t("init.carpetas"))
            return
        if os.path.abspath(self.carpeta_in.get()) == os.path.abspath(self.carpeta_out.get()):
            messagebox.showwarning(t("init.iguales_t"), t("init.iguales"))
            return
        if self.visible.get() and not self.posicion["definida"]:
            messagebox.showwarning(t("init.pos_t"), t("init.pos"))
            return

        if self.usar_tsa.get() and not self.tsa_url.get().strip().lower().startswith(("http://", "https://")):
            messagebox.showwarning(t("init.tsa_t"), t("init.tsa"))
            return
        for etiqueta, ruta, clave in (
            [(t("ui.firma1"), self.p12_1.get(), self.clave_1.get())]
            + ([(t("ui.firma2"), self.p12_2.get(), self.clave_2.get())] if self.usar_2.get() else [])
        ):
            ok, texto = revisar_firma(ruta, clave)
            if not ok:
                messagebox.showerror(t("init.problema_firma", etiqueta=etiqueta), texto)
                return

        try:
            self.firmante1 = cargar_firmante(self.p12_1.get(), self.clave_1.get())
            self.firmante2 = (cargar_firmante(self.p12_2.get(), self.clave_2.get())
                              if self.usar_2.get() else None)
        except Exception:
            messagebox.showerror(t("init.firma_no_abre_t"), t("init.firma_no_abre"))
            return

        os.makedirs(self.carpeta_out.get(), exist_ok=True)
        self._continuar.set()
        self._detener.clear()
        self._estado_botones(True)
        self._t0 = time.time()
        self._pausa_total = 0.0
        self._pausa_ini = None
        self._hechos = 0
        self._n_firmados = 0
        self._suma_firmados = 0.0
        self._total = 0
        self._corriendo = True
        self._tick()
        datos = {
            "entrada": self.carpeta_in.get(),
            "salida": self.carpeta_out.get(),
            "visible": self.visible.get(),
            "pos": {k: (dict(v) if isinstance(v, dict) else v) for k, v in self.posicion.items()},
            "pdfs": self._lista_pdfs(),
            "omitir": self.omitir.get(),
            "recursivo": self.recursivo.get(),
            "qr": self.qr.get(),
            "evitar": self.evitar.get(),
            "tsa": ((self.tsa_url.get(), self.tsa_user.get(), self.tsa_pass.get())
                    if self.usar_tsa.get() else None),
        }
        threading.Thread(target=self._trabajo, args=(datos,), daemon=True).start()

    def _datos_firmante(self, etiqueta, firmante):
        cert = firmante.signing_cert
        nombre = nombre_titular(cert)
        vence = cert["tbs_certificate"]["validity"]["not_after"].native
        return (etiqueta, nombre, f"{vence:%d/%m/%Y}")

    def _trabajo(self, datos):
        entrada, salida, pdfs = datos["entrada"], datos["salida"], datos["pdfs"]
        total = len(pdfs)
        self._total = total
        if total == 0:
            def vacio():
                self._corriendo = False
                self._estado_botones(False)
                self.tiempo.set("")
                messagebox.showinfo(t("fin.vacio_t"), t("fin.vacio"))
            self.after(0, vacio)
            return

        inicio = self._t0
        visible = datos["visible"]
        pos = datos["pos"]
        # un solo cliente TSA para toda la corrida: evita consultas de medición repetidas
        tsa = crear_sellador(*datos["tsa"]) if datos["tsa"] else None
        fracciones = {n: c for n, c in pos["cajas"].items() if n == 1 or self.firmante2 is not None}
        registros = []
        self.after(0, lambda: self.barra.configure(maximum=total, value=0))

        for i, rel in enumerate(pdfs, 1):
            if self._detener.is_set():
                break
            if not self._continuar.is_set():
                self.after(0, lambda: self.estado.set(t("estado.en_pausa")))
                self._continuar.wait()
                if self._detener.is_set():
                    break
            self.after(0, lambda n=rel, i=i: self.estado.set(t("estado.firmando", i=i, total=total, nombre=n)))
            t_ini = time.time()
            origen = os.path.join(entrada, rel)
            destino = os.path.join(salida, rel)
            estado, mensaje, ajuste = "firmado", "", None
            try:
                kb = os.path.getsize(ruta_larga(origen)) / 1024
            except OSError:
                kb = 0.0
            try:
                if datos["omitir"] and os.path.exists(ruta_larga(destino)):
                    estado = "omitido"
                else:
                    os.makedirs(ruta_larga(os.path.dirname(destino)), exist_ok=True)
                    if visible:
                        pagina, cajas, ajuste = cajas_para_pdf(
                            origen, pos["modo"], pos["numero"], fracciones, datos["evitar"])
                    else:
                        pagina, cajas = 0, {1: None, 2: None}
                    firmantes = [(self.firmante1, "Firma1", cajas[1])]
                    if self.firmante2 is not None:
                        firmantes.append((self.firmante2, "Firma2", cajas[2]))
                    firmar_un_pdf(origen, destino, firmantes, pagina, visible, tsa, datos["qr"])
            except SinEspacio as e:
                estado, mensaje = "sin_espacio", str(e)
            except Exception as e:
                estado, mensaje = "error", describir_error(e)
            dur = time.time() - t_ini
            registros.append({"archivo": rel, "estado": estado, "segundos": dur, "kb": kb,
                              "hora": time.time(), "mensaje": mensaje, "ajuste": ajuste})
            self._hechos = i
            if estado == "firmado":
                self._n_firmados += 1
                self._suma_firmados += dur
            self.after(0, lambda i=i: self.barra.configure(value=i))

        fin = time.time()
        detenido = self._detener.is_set()

        def terminar():
            self._corriendo = False
            self._cerrar_pausa()
            self._estado_botones(False)
            modo = pos["modo"]
            est = {
                "inicio": inicio, "fin": fin, "pausa_s": self._pausa_total, "detenido": detenido,
                "total": total, "registros": registros, "visible": visible, "qr": datos["qr"],
                "pagina": {"primera": t("pos.pagina_informe_primera"),
                           "ultima": t("pos.pagina_informe_ultima")}.get(modo, str(pos["numero"])),
                "tsa": datos["tsa"][0] if datos["tsa"] else None, "recursivo": datos["recursivo"],
                "evitar": datos["evitar"],
                "entrada": entrada, "salida": salida,
                "equipo": socket.gethostname(), "usuario": os.environ.get("USERNAME") or os.environ.get("USER", "?"),
                "firmantes": [self._datos_firmante(t("ui.firma1"), self.firmante1)] +
                             ([self._datos_firmante(t("ui.firma2"), self.firmante2)] if self.firmante2 is not None else []),
            }
            ok = sum(1 for r in registros if r["estado"] == "firmado")
            omit = sum(1 for r in registros if r["estado"] == "omitido")
            errores = [r for r in registros if r["estado"] == "error"]
            sin_esp = [r for r in registros if r["estado"] == "sin_espacio"]
            pend = total - len(registros)
            extra = t("estado.extra_omitidos", n=omit) if omit else ""
            if sin_esp:
                extra += t("estado.extra_sin_espacio", n=len(sin_esp))
            if detenido:
                self.estado.set(t("estado.detenido", ok=ok, extra=extra, err=len(errores), pend=pend))
            else:
                self.estado.set(t("estado.terminado", ok=ok, extra=extra, err=len(errores)))
            self.tiempo.set(t("tiempo.final", a=fmt_fecha(inicio)[11:], b=fmt_fecha(fin)[11:],
                              c=fmt_hms(fin - inicio)))
            ruta_err = os.path.join(salida, "errores_firmado.txt")
            if errores:
                with open(ruta_err, "w", encoding="utf-8") as f:
                    f.write("\n".join(f"{r['archivo']}: {r['mensaje']}" for r in errores))
            try:
                ruta_txt, ruta_csv = guardar_informes(est)
                pie = t("fin.informe_pie", txt=os.path.basename(ruta_txt), csv=os.path.basename(ruta_csv))
            except Exception:
                pie = t("fin.informe_fallo")
            cuerpo = resumen_corto(est) + pie
            if detenido:
                messagebox.showwarning(t("fin.detenido_t"), cuerpo + t("fin.detenido_texto"))
            elif errores or sin_esp:
                aviso = t("fin.errores_en", ruta=ruta_err) if errores else ""
                messagebox.showwarning(t("fin.avisos_t"), cuerpo + aviso)
            else:
                messagebox.showinfo(t("fin.listo_t"), cuerpo)

        self.after(0, terminar)


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
