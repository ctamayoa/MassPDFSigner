"""Informes de cada corrida: resumen de texto y registro CSV."""
import csv
import datetime
import os
import statistics

from ._version import __version__
from .archivos import ruta_larga


def fmt_hms(segundos):
    segundos = int(max(0, round(segundos)))
    return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}:{segundos % 60:02d}"


def fmt_fecha(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


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
    L = []
    L.append(f"INFORME DE FIRMADO MASIVO - Firmador Masivo PDF v{__version__}")
    L.append("=" * 62)
    L.append(f"Estado final        : {'DETENIDO por el usuario' if e['detenido'] else 'COMPLETADO'}")
    L.append(f"Hora de inicio      : {fmt_fecha(e['inicio'])}")
    L.append(f"Hora de término     : {fmt_fecha(e['fin'])}")
    L.append(f"Duración total      : {fmt_hms(total_s)}")
    L.append(f"Tiempo en pausa     : {fmt_hms(e['pausa_s'])}")
    L.append(f"Tiempo efectivo     : {fmt_hms(efectivo)}")
    L.append("")
    L.append("RESULTADO")
    L.append(f"PDFs encontrados    : {e['total']}")
    L.append(f"Firmados            : {len(hechos)}")
    L.append(f"Omitidos (ya estaban): {omit}")
    L.append(f"Con posición ajustada: {len(ajustados)}")
    L.append(f"SIN ESPACIO (no firmados): {len(sine)}")
    L.append(f"Con error           : {len(err)}")
    L.append(f"Pendientes          : {pendientes}")
    L.append(f"Carpetas procesadas : {carpetas_total} (con PDFs firmados: {carpetas_firm})")
    L.append(f"Tamaño firmado      : {mb:.1f} MB")
    L.append("")
    L.append("RENDIMIENTO")
    if seg:
        L.append(f"Promedio por PDF    : {sum(seg) / len(seg):.2f} s")
        L.append(f"Mediana             : {statistics.median(seg):.2f} s")
        L.append(f"Más rápido          : {min(seg):.2f} s")
        L.append(f"Más lento           : {max(seg):.2f} s ({max(hechos, key=lambda r: r['segundos'])['archivo']})")
        if efectivo > 0:
            L.append(f"Velocidad           : {len(hechos) / (efectivo / 60):.1f} PDFs por minuto")
    else:
        L.append("(no se firmó ningún PDF en esta corrida)")
    L.append("")
    L.append("CONFIGURACIÓN USADA")
    for etiqueta, nombre, vence in e["firmantes"]:
        L.append(f"{etiqueta:<20}: {nombre} (certificado vigente hasta {vence})")
    L.append(f"Firma visible       : {'sí' if e['visible'] else 'no'}" +
             (f" (página {e['pagina']}, con QR: {'sí' if e['qr'] else 'no'})" if e["visible"] else ""))
    L.append(f"Evitar tapar contenido: {'sí' if e.get('evitar') else 'no'}")
    L.append(f"Sello de tiempo     : {e['tsa'] if e['tsa'] else 'no'}")
    L.append(f"Incluye subcarpetas : {'sí' if e['recursivo'] else 'no'}")
    L.append(f"Carpeta de origen   : {e['entrada']}")
    L.append(f"Carpeta de salida   : {e['salida']}")
    L.append(f"Equipo / usuario    : {e['equipo']} / {e['usuario']}")
    if sine:
        L.append("")
        L.append("ARCHIVOS SIN ESPACIO LIBRE (NO SE FIRMARON, revisar a mano)")
        for r in sine:
            L.append(f"- {r['archivo']}")
    if err:
        L.append("")
        L.append("ARCHIVOS CON ERROR")
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
    L = [f"Inicio:   {fmt_fecha(e['inicio'])}",
         f"Término:  {fmt_fecha(e['fin'])}",
         f"Duración: {fmt_hms(total_s)}" + (f"  (pausa: {fmt_hms(e['pausa_s'])})" if e["pausa_s"] >= 1 else ""),
         "",
         f"Firmados: {len(hechos)}   Omitidos: {omit}   Errores: {err}" + (f"   Pendientes: {pend}" if pend else "")]
    if ajust:
        L.append(f"Con posición ajustada: {ajust}")
    if sine:
        L.append(f"SIN ESPACIO LIBRE (no se firmaron): {sine}  -> ver el CSV")
    if hechos and efectivo > 0:
        L.append(f"Promedio: {sum(r['segundos'] for r in hechos) / len(hechos):.2f} s por PDF "
                 f"({len(hechos) / (efectivo / 60):.1f} PDFs/min)")
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
