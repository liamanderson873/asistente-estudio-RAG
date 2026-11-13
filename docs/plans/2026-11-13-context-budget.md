# Reducir el contexto enviado al generador

Diseño aprobado en el chat: probar tres fragmentos frente a cinco con Qwen 2.5 3B. Cambiar una sola variable y conservar controles de citas y abstención.

1. Recuperar siempre los mismos cinco resultados con los mismos candidatos y el mismo RRF. Recortar únicamente el contexto del generador y validar referencias exclusivamente contra los fragmentos enviados. Configurar un límite entre uno y cinco; mantener inicialmente cinco hasta revisar la prueba real.
2. Ejecutar las dos preguntas de desarrollo ya utilizadas, con los mismos resultados recuperados por pregunta. Alternar el orden de comparación: 5/3 para JOIN y 3/5 para la pregunta sin respuesta. Guardar tiempos de generación separados de recuperación y métricas de tokens de Ollama. No ajustar con holdout.
3. Revisar manualmente las respuestas y los fragmentos. Adoptar tres si mantiene las citas y la abstención y reduce la espera observada; en caso contrario conservar cinco y registrar el fallo. No presentar cuatro ejecuciones como evidencia de calidad general.
4. Ejecutar los tests de regresión sobre presupuesto/contexto y citas omitidas, la suite completa con PostgreSQL y Ruff. Documentar el resultado, actualizar los mapas y dejar la web con la configuración elegida.
