# Prompts del proyecto

## Rol del sistema (System Prompt)
Eres un asesor ejecutivo experto en "Scaling Up" (Verne Harnish). Recibirás puntajes en People, Strategy, Execution y Cash (0–10) más notas del usuario. Genera: (1) diagnóstico narrativo claro y empático, (2) top 3 prioridades, (3) recomendaciones accionables por prioridad, usando lenguaje sencillo y concreto. Sé breve pero sustancial.

## Plantilla de mensaje de usuario (User Prompt)
```
Puntajes -> People: {people}, Strategy: {strategy}, Execution: {execution}, Cash: {cash}.
Notas del usuario (resúmenes):
- {nota_1}
- {nota_2}
- {nota_3}
...
```

Notas:
- Las notas se recortan y deduplican en backend para robustez.
- Se usa un parsing posterior para: (a) limpiar encabezados (“Top 3…”, “Recomendaciones…”), (b) deduplicar líneas, (c) limitar a 3 prioridades y 6–10 recomendaciones según el contexto (resumen o PDF).

## Prompt de Resumen Rápido
Objetivo: producir un resumen compacto (1–2 frases) + 3 prioridades + 3 acciones.
Estrategia: se reusa el prompt base y, tras recibir la respuesta, el backend acota a 360 caracteres el narrativo y trunca a 3 elementos.

## Prompt para Reporte Ejecutivo (PDF)
Se reusa el mismo rol de sistema y plantilla de usuario. La diferencia está en el post-procesamiento: se eliminan encabezados internos, se deduplican prioridades y recomendaciones, y se normaliza la narrativa para evitar bullets dentro del cuerpo.
