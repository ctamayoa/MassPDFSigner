# Guía de usuario

Esta guía explica cómo firmar un lote de PDFs con Firmador Masivo PDF.

## Instalación

Descarga de la sección **Releases** una de estas dos opciones:

- **Instalador** (`FirmadorPDF-Setup-X.Y.Z.exe`): ejecútalo y sigue el asistente. No pide permisos de administrador. Después lo abres desde el menú Inicio.
- **Portátil** (`FirmadorPDF-portable-X.Y.Z.zip`): no se instala. Clic derecho → *Extraer todo*, abre la carpeta que se crea y ejecuta `FirmadorPDF.exe`. Útil si trabajas desde una memoria USB, en un equipo prestado o de un cliente, o si en tu equipo no puedes instalar programas. No abras el `.exe` sin extraer antes el `.zip`.

Para quitarlo: el instalado, desde *Aplicaciones instaladas* de Windows; el portátil, borrando la carpeta.

## Antes de empezar

Necesitas:

- Tu archivo de firma electrónica (`.p12` o `.pfx`) y su contraseña. Si vas a usar dos firmas, necesitas los dos archivos y las dos contraseñas.
- Una carpeta con los PDFs que quieres firmar.
- Una carpeta **distinta** donde se guardarán los PDFs firmados. Los originales nunca se modifican.

## Paso a paso

### 0. Idioma

Arriba a la derecha puedes elegir **español, English o Português**. La ventana se vuelve a dibujar sin perder lo que ya escribiste, y el programa recuerda tu elección. Solo se puede cambiar cuando no hay una firma en curso. El texto de la firma visible, el QR y los informes salen en el idioma elegido.

### 1. Elige las firmas

En **Firma 1**, pulsa **Buscar...** y elige tu archivo `.p12`. Escribe la contraseña.

Si necesitas una segunda firma, deja marcada **Usar segunda firma** y repite lo mismo en **Firma 2**. Si solo usas una, desmarca esa casilla.

Pulsa **Validar firmas** para comprobar que la contraseña es correcta y que la firma está vigente. El programa te avisa si está vencida, si todavía no es válida o si vence en menos de 30 días.

### 2. Elige las carpetas

- **Carpeta con PDFs**: donde están los documentos.
- **Guardar firmados en**: donde se dejarán los firmados.

Opciones:

- **Incluir subcarpetas**: firma también los PDFs de las carpetas internas. En la salida se repite la misma estructura de carpetas.
- **Omitir los que ya están en la carpeta de salida**: sirve para continuar si el proceso se interrumpió; no vuelve a firmar lo que ya está hecho.
- **Evitar tapar el contenido del documento**: si bajo el recuadro de la firma hay texto o imágenes, mueve las firmas a un lugar libre de la página. Si no hay ningún lugar libre, **ese PDF no se firma** y queda anotado en el informe como «sin espacio». Los gráficos y las líneas no cuentan como contenido.

### 3. Dibuja dónde va la firma

Con **Mostrar firma visible en el documento** marcada, pulsa **Elegir posición de las firmas...**. Se abre un PDF de ejemplo:

1. Elige la página donde irá la firma: primera, última o un número.
2. Arrastra el mouse sobre la hoja para dibujar el recuadro de la Firma 1 (rojo). Después dibuja el de la Firma 2 (azul).
3. Si no te gusta, vuelve a dibujar. Pulsa **Aceptar posición**.

La posición se guarda como proporción de la página, así que se adapta a hojas de distinto tamaño.

Si quieres que el recuadro lleve un **código QR**, deja marcada la casilla correspondiente.

### 4. Sello de tiempo (opcional)

Marca **Agregar sello de tiempo a cada firma** si quieres que un servidor externo certifique la hora de la firma. Por defecto viene un servidor gratuito. Pulsa **Probar servidor** para comprobar que responde. Antes de usarlo, lee [validez-legal.md](validez-legal.md): un servidor gratuito no equivale a uno acreditado.

### 5. Firma

Pulsa **FIRMAR DOCUMENTOS**. Verás el avance, el tiempo transcurrido y una estimación del tiempo restante.

- **Pausar**: termina el archivo actual y espera. **Reanudar** continúa.
- **Detener**: termina el archivo actual y para. Lo ya firmado se conserva. Para continuar, vuelve a pulsar **FIRMAR** con las mismas carpetas y la casilla de omitir marcada.

## Qué verás al terminar

En la carpeta de salida quedan los PDFs firmados y estos archivos:

| Archivo | Contenido |
| --- | --- |
| `resumen_firmado_AAAA-MM-DD_HHMMSS.txt` | Resumen de la corrida: cantidades, tiempos, configuración usada y lista de problemas. |
| `registro_firmado_AAAA-MM-DD_HHMMSS.csv` | Una fila por PDF con su estado (`firmado`, `omitido`, `error`, `sin_espacio`). Se abre en Excel; el separador es `;`. |
| `errores_firmado.txt` | Solo aparece si hubo errores: archivo y motivo. |

## Problemas frecuentes

**«El archivo está dañado o no es un PDF válido.»** El documento no se puede abrir. Ábrelo con tu lector de PDF: si tampoco abre, hay que reemplazarlo por una copia buena.

**«El PDF está protegido con contraseña o cifrado.»** Quítale la protección antes de firmarlo.

**«No se pudo leer o guardar el archivo.»** Suele ser un archivo abierto en otro programa o una carpeta sin permisos. Ciérralo e inténtalo de nuevo.

**«SIN ESPACIO»**: no hay un lugar libre del tamaño de las firmas. Firma ese documento aparte, o desmarca **Evitar tapar el contenido** si aceptas que la firma quede sobre el texto.

**Mi lector de PDF dice «validez desconocida»**: es normal con muchos certificados. Ver [validez-legal.md](validez-legal.md).

**Windows o el antivirus bloquean el programa**: el `.exe` no está firmado digitalmente. Comprueba su SHA256 contra el publicado en la Release, o compílalo tú: [compilar.md](compilar.md).

## Buenas prácticas

- Haz primero una prueba con 2 o 3 documentos.
- Revisa el `.csv` al terminar, sobre todo los `error` y `sin_espacio`.
- Cuida tu archivo `.p12` y su contraseña: quien los tenga puede firmar en tu nombre.
