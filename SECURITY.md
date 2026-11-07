# Política de seguridad

## Versiones con soporte

Se corrigen los problemas de seguridad en la última versión publicada de la serie 1.x.

## Cómo reportar una vulnerabilidad

**No abras un issue público.** Usa el reporte privado de GitHub: pestaña **Security** del repositorio → **Report a vulnerability**.

Incluye, si puedes:

- Qué versión usas y en qué sistema.
- Pasos para reproducirlo.
- Qué impacto crees que tiene.

Responderemos en cuanto sea posible. Cuando haya corrección, la publicaremos en una nueva versión y lo anotaremos en el `CHANGELOG`.

## Muy importante: no compartas datos sensibles

En ningún reporte, issue ni pull request adjuntes:

- archivos `.p12` / `.pfx` reales,
- contraseñas o claves,
- PDFs reales ni datos de clientes.

Si necesitas mostrar un caso, usa un certificado de prueba y un PDF inventado. Si por error expusiste un certificado, **revócalo y solicita uno nuevo** a tu entidad certificadora: borrar el mensaje no basta.

## Qué se considera en alcance

- Filtración de contraseñas o claves privadas (en pantalla, informes o archivos temporales).
- Escritura o lectura de archivos fuera de las carpetas elegidas.
- Firmas generadas con un certificado distinto al elegido.
- Ejecución de código a partir de un PDF o un `.p12` manipulado.
