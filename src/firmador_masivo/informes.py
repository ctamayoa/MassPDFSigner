"""Informes de cada corrida: resumen de texto y registro CSV.

El resumen y el mensaje del CSV salen en el idioma de la interfaz; los encabezados y los
estados del CSV (firmado, omitido, error, sin_espacio) no cambian, para no romper planillas."""
import csv
import datetime
import os
import statistics

from ._version import __version__
from .archivos import ruta_larga
from .i18n import t


def fmt_hms(segundos):
    segundos = int(max(0, round(segundos)))
    return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}:{segundos % 60:02d}"


def fmt_fecha(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def _si_no(v):
    return t("inf.si") if v else t("inf.no")


def armar_resumen(e):
    """Texto completo del informe. 'e' es el diccionario de estadísticas de la corrida."""
    total_s = e["fin"] - e["inicio"]
    efectivo = max(0.0, total_s - e["pausa_s"])
    hechos = [r for r in e["registros"] if r["estado"] == "firmado"]
    seg = [r["segundos"] for r in hechos]
    omit = sum(1 for r in e["registros"] if r["estado"] == "omitido")
    err = [r for r in e["registros"] if r["estado"] == "error"]
    sine = [r for r in e["registros"] if r["estado"] == "sin_espacio"]
    ajustados = [r for r in hechos if r.get("ajuste")]
    pendientes = e["total"] - len(e["registros"])
    carpetas_total = len({os.path.dirname(r["archivo"]) for r in e["registros"]})
    carpetas_firm = len({os.path.dirname(r["archivo"]) for r in hechos})
    mb = sum(r["kb"] for r in hechos) / 1024
    estado = t("inf.estado_detenido") if e["detenido"] else t("inf.estado_completado")
    L = []
    L.append(t("inf.titulo", version=__version__))
    L.append("=" * 62)
    L.append(t("inf.estado", v=estado))
    L.append(t("inf.hora_inicio", v=fmt_fecha(e["inicio"])))
    L.append(t("inf.hora_fin", v=fmt_fecha(e["fin"])))
    L.append(t("inf.duracion", v=fmt_hms(total_s)))
    L.append(t("inf.pausa", v=fmt_hms(e["pausa_s"])))
    L.append(t("inf.efectivo", v=fmt_hms(efectivo)))
    L.append("")
    L.append(t("inf.resultado"))
    L.append(t("inf.encontrados", v=e["total"]))
    L.append(t("inf.firmados", v=len(hechos)))
    L.append(t("inf.omitidos", v=omit))
    L.append(t("inf.ajustados", v=len(ajustados)))
    L.append(t("inf.sin_espacio", v=len(sine)))
    L.append(t("inf.con_error", v=len(err)))
    L.append(t("inf.pendientes", v=pendientes))
    L.append(t("inf.carpetas", total=carpetas_total, firm=carpetas_firm))
    L.append(t("inf.tamano", v=mb))
    L.append("")
    L.append(t("inf.rendimiento"))
    if seg:
        L.append(t("inf.promedio", v=sum(seg) / len(seg)))
        L.append(t("inf.mediana", v=statistics.median(seg)))
        L.append(t("inf.rapido", v=min(seg)))
        L.append(t("inf.lento", v=max(seg), archivo=max(hechos, key=lambda r: r["segundos"])["archivo"]))
        if efectivo > 0:
            L.append(t("inf.velocidad", v=len(hechos) / (efectivo / 60)))
    else:
        L.append(t("inf.ninguno"))
    L.append("")
    L.append(t("inf.config"))
    for etiqueta, nombre, vence in e["firmantes"]:
        L.append(t("inf.certificado", etiqueta=etiqueta, nombre=nombre, vence=vence))
    detalle = t("inf.visible_detalle", pagina=e["pagina"], qr=_si_no(e["qr"])) if e["visible"] else ""
    L.append(t("inf.visible", v=_si_no(e["visible"])) + detalle)
    L.append(t("inf.evitar", v=_si_no(e.get("evitar"))))
    L.append(t("inf.tsa", v=e["tsa"] if e["tsa"] else t("inf.no")))
    L.append(t("inf.subcarpetas", v=_si_no(e["recursivo"])))
    L.append(t("inf.origen", v=e["entrada"]))
    L.append(t("inf.salida", v=e["salida"]))
    L.append(t("inf.equipo", equipo=e["equipo"], usuario=e["usuario"]))
    if sine:
        L.append("")
        L.append(t("inf.lista_sin_espacio"))
        for r in sine:
            L.append(f"- {r['archivo']}")
    if err:
        L.append("")
        L.append(t("inf.lista_errores"))
        for r in err:
            L.append(f"- {r['archivo']}: {r['mensaje']}")
    return "\n".join(L)


def resumen_corto(e):
    """Versión breve para mostrar en la ventana al terminar."""
    total_s = e["fin"] - e["inicio"]
    efectivo = max(0.0, total_s - e["pausa_s"])
    hechos = [r for r in e["registros"] if r["estado"] == "firmado"]
    omit = sum(1 for r in e["registros"] if r["estado"] == "omitido")
    err = sum(1 for r in e["registros"] if r["estado"] == "error")
    sine = sum(1 for r in e["registros"] if r["estado"] == "sin_espacio")
    ajust = sum(1 for r in hechos if r.get("ajuste"))
    pend = e["total"] - len(e["registros"])
    L = [t("corto.inicio", v=fmt_fecha(e["inicio"])),
         t("corto.fin", v=fmt_fecha(e["fin"])),
         t("corto.duracion", v=fmt_hms(total_s)) + (t("corto.pausa", v=fmt_hms(e["pausa_s"])) if e["pausa_s"] >= 1 else ""),
         "",
         t("corto.conteo", ok=len(hechos), omit=omit, err=err) + (t("corto.pendientes", v=pend) if pend else "")]
    if ajust:
        L.append(t("corto.ajustadas", v=ajust))
    if sine:
        L.append(t("corto.sin_espacio", v=sine))
    if hechos and efectivo > 0:
        L.append(t("corto.promedio", prom=sum(r["segundos"] for r in hechos) / len(hechos),
                   vel=len(hechos) / (efectivo / 60)))
    return "\n".join(L)


def guardar_informes(e):
    """Guarda resumen (.txt) y registro por archivo (.csv, abre en Excel) en la carpeta de salida."""
    sello = datetime.datetime.fromtimestamp(e["inicio"]).strftime("%Y-%m-%d_%H%M%S")
    base = ruta_larga(e["salida"])
    ruta_txt = os.path.join(base, f"resumen_firmado_{sello}.txt")
    ruta_csv = os.path.join(base, f"registro_firmado_{sello}.csv")
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(armar_resumen(e))
    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["hora_fin", "carpeta", "archivo", "estado", "posicion", "ajuste_pt (+sube -baja)",
                    "segundos", "tamano_kb", "mensaje"])
        for r in e["registros"]:
            if r["estado"] == "firmado":
                posicion = "ajustada" if r.get("ajuste") else "original"
            elif r["estado"] == "sin_espacio":
                posicion = "SIN ESPACIO - NO FIRMADO"
            else:
                posicion = ""
            ajuste = r.get("ajuste") or ""
            w.writerow([fmt_fecha(r["hora"]), os.path.dirname(r["archivo"]), os.path.basename(r["archivo"]),
                        r["estado"], posicion, ajuste, f"{r['segundos']:.2f}".replace(".", ","),
                        f"{r['kb']:.0f}", r["mensaje"]])
    return ruta_txt, ruta_csv
