# Validez de las firmas y sello de tiempo

> Nota informativa. No es asesoría legal. Si el documento tiene consecuencias legales o tributarias, confirma los requisitos con tu abogado o con la institución que lo recibirá.

## Qué hace (y qué no hace) este programa

Firmador Masivo PDF **aplica una firma digital** a cada PDF con el certificado que tú le entregas. No emite certificados ni es una entidad de certificación. Por eso:

- La **integridad** la garantiza la firma: si alguien modifica el PDF después de firmado, el lector lo detecta.
- La **identidad** y la **validez legal** dependen del certificado: quién lo emitió y si esa entidad es reconocida donde lo vas a usar.

En Ecuador, la ley reconoce los certificados emitidos por entidades de certificación acreditadas por ARCOTEL. Si tu certificado viene de una de ellas, la firma tiene respaldo legal por el certificado, no por este programa.

## Por qué mi lector de PDF dice «validez desconocida»

Es el aviso más común y no significa que la firma esté mal hecha. Un lector de PDF (por ejemplo Adobe Acrobat) comprueba dos cosas distintas:

1. **¿El documento cambió después de firmarse?** Si el lector dice que no se modificó, la firma está íntegra.
2. **¿Confío en quien emitió el certificado?** El lector solo confía en entidades cuyo certificado raíz está en su lista de confianza. Si la raíz de tu entidad certificadora no está ahí, muestra «validez desconocida» o «identidad del firmante desconocida».

Es decir, el aviso suele ser sobre la **confianza en la entidad**, no sobre el documento. Cada lector mantiene su propia lista, por eso el mismo PDF puede verse distinto en programas diferentes.

### Cómo resolverlo

- Pide a tu entidad certificadora su **certificado raíz** (y los intermedios) e instálalos como de confianza en el lector que usarás para verificar. Cada lector tiene su propio menú para esto (en Acrobat: Preferencias → Firmas → Identidades y certificados de confianza).
- O verifica el documento con el **validador oficial** que ofrezca tu entidad o la autoridad de tu país.

El sello de tiempo **no soluciona** este aviso: certifica *cuándo* se firmó, no *en quién* se confía.

## Sello de tiempo (TSA)

Una firma digital incluye la hora del equipo donde se firmó, que cualquiera puede cambiar. Un **sello de tiempo** (RFC 3161) lo resuelve: un servidor externo firma el momento exacto, y eso prueba que el documento existía en esa fecha. Además ayuda a que la firma siga siendo verificable aunque el certificado venza después.

### Gratuita vs. acreditada

| | Servidor gratuito (por defecto: DigiCert) | Entidad acreditada en el país |
| --- | --- | --- |
| Costo | Sin costo | De pago |
| Fija la hora de forma técnica | Sí | Sí |
| Reconocimiento legal en Ecuador | **No acreditado por ARCOTEL** | Sí |
| Pide usuario y clave | No | Normalmente sí |

Con un servidor gratuito, el sello sirve como evidencia técnica, pero **puede no ser aceptado** si la norma o la institución receptora exige un sello de una entidad acreditada. Si ese es tu caso, usa el servidor de tu entidad certificadora: en el programa escribe su dirección y, si lo pide, su usuario y clave, y pulsa **Probar servidor**.

Si no tienes ese requisito, puedes dejar el sello desactivado: las firmas siguen siendo válidas y el proceso es más rápido (cada sello añade una consulta por firma).

## Resumen

| Pregunta | Respuesta corta |
| --- | --- |
| ¿La firma detecta cambios posteriores? | Sí. |
| ¿Quién garantiza la identidad? | El certificado y su entidad emisora. |
| ¿Por qué «validez desconocida»? | El lector no tiene la raíz de tu entidad en su lista de confianza. |
| ¿El sello de tiempo lo arregla? | No: prueba la fecha, no la confianza. |
| ¿Sirve el sello gratuito legalmente? | Como evidencia técnica sí; no está acreditado en Ecuador. |

## Verificador del programa

**Verificar documentos...** comprueba lo que se puede comprobar sin conexión: que el documento no cambió desde la firma, quién firmó, cuándo, si el certificado estaba vigente en ese momento y, si cargas los certificados raíz de la entidad, si el emisor es reconocido. No consulta revocación en línea ni emite un dictamen legal; su resultado es una ayuda técnica y no reemplaza la validación oficial de la entidad de certificación.
