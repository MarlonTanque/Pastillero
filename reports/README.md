# Evidencia pública y resultados locales

`public-validation-summary.json` resume la validación del 22 de octubre de 2026. No representa una nueva ejecución de los 204 casos en la fecha de publicación del repositorio. La preparación del push tiene comprobaciones separadas con su fecha y resultados.

`study-source-coverage.json` conserva el inventario de las guías educativas. Algunas entradas corresponden a la forma redactada de configuración local, deliberadamente no distribuida. En otra computadora deben preparar su configuración local y regenerar las guías para verificar ese inventario.

Los registros completos, capturas de Firebase, datos de cuentas, copias de configuración y recibos ligados a esta computadora permanecen locales y están ignorados por Git. Los verificadores históricos `verify_project.py`, `verify_version2.py`, `verify_unification.py` y `verify_compilation.py` requieren respaldos, informes y/o compilaciones locales: no son comprobaciones listas para ejecutar en un clon limpio. No hay que crear resultados ficticios para satisfacerlos.

Las pruebas portables de React, reglas, backend y Android se describen en `docs/COLABORACION_GITHUB.md`. Ninguna exige conectar el hardware para validar software.
