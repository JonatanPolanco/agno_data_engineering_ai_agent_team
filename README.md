Este proyecto implementa un orquestador y un conjunto de agentes especializados 
(Arquitectura, ETL/ELT, Analítica & SQL, DataOps/QA, Estratégico y Search (web & documents)),
apoyados por modelos Gemini (2.5 Pro y 2.0 Flash) y RAG en Vertex AI.

Regla operativa clave: Antes de generar código (HOW) cada propuesta debe producir un
Decision Memo respondiendo: WHAT, WHY, WHO, WHERE, WHEN. Sólo tras validar
impacto/risgo (Estratégico + DataOps/QA) se genera e implementa código.

Objetivo: Dar soporte senior a ingenieros de analítica y de datos mediante: 
- Recomendaciones técnicas y de arquitectura. 
- Generación y validación de código (Gemini 2.5 pro). 
- Auditoría de estándares internos y calidad de datos. 
- Evaluación de riesgos e impacto en negocio. 
- Acceso a conocimiento fresco vía web search.

El orquestador enruta cada tarea al agente adecuado, combina RAG especializado (libros y documentación oficial) 
con un “Knowledge Hub” compartido y devuelve respuestas consolidadas.

libros usados como base de conocimiento interna (RAG): https://github.com/JonatanPolanco/data_engineering__books
