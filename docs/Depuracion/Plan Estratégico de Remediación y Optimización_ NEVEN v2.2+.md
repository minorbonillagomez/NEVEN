### Plan Estratégico de Remediación y Optimización: NEVEN v2.2+

Este documento constituye la directriz técnica de cumplimiento obligatorio para la estabilización y blindaje de NEVEN. Como Arquitecto Senior, el objetivo central es la transición de un prototipo avanzado hacia un sistema de grado de producción, eliminando vulnerabilidades de diseño y saneando el núcleo del sistema mediante la remoción exhaustiva de deuda técnica identificada en las auditorías de mayo de 2026\.

#### 1\. Fortalecimiento de la Seguridad Crítica (Aislamiento de Nivel OS)

La arquitectura actual depende de  **SandboxVerifier** , el cual opera mediante filtrado de patrones de texto. Si bien cuenta con una cobertura de 154 tests, el análisis de riesgo en la "Evaluación Doctoral" (Sección 2.2) admite una limitación estructural: la validación basada en patrones es susceptible de bypass ante atacantes motivados que empleen técnicas de ofuscación complejas.Se instruye la transición inmediata hacia un esquema de aislamiento gestionado por el Kernel del Sistema Operativo para reducir drásticamente la superficie de ataque.

##### Comparativa Técnica: Seguridad Basada en Patrones vs. Aislamiento de Kernel

Característica,Situación Actual (Basada en Patrones),Mejora Propuesta (Aislamiento OS-Level)  
Mecanismo Primario,Análisis de strings y listas de bloqueo en  SandboxVerifier .,Restricción de privilegios de proceso vía  AppContainer  (Win32).  
Punto de Control,Espacio de usuario (User-space).,Nivel de Kernel/Sistema Operativo.  
Riesgo Identificado,Bypass mediante ofuscación no detectada Doc 2.2.,Inviolable mediante código; denegación por política de hardware/red.  
Mantenimiento,Actualización reactiva de blocklists de R/Julia/Python.,Definición estática de capacidades de proceso (Capabilities).  
Dependencias,Lógica interna de  SandboxVerifier.cc .,API de seguridad nativa de Windows / perfiles  seccomp .

#### 2\. Depuración Arquitectónica y Saneamiento de Deuda Técnica

La "Auditoría de Código Muerto C++" Documento 10 revela una proliferación de componentes huérfanos que pertenecen a la arquitectura de  *embedding*  directo, la cual ha sido totalmente deprecada en favor de la arquitectura de procesos hijos coordinados. El mantenimiento de estos archivos compromete la higiene de la compilación y aumenta la complejidad cognitiva del sistema.

##### Eliminación de Componentes Obsoletos

Se ordena la remoción definitiva de los siguientes elementos del repositorio y de los archivos  **CMakeLists.txt** :

1. **Cadena de Carga Legacy:**  Eliminar  **RuntimeLoader.cc** ,  **AutoLoader.cc**  y  **GCMonitor.cc**  (Common/). Estos componentes dependían de la interfaz  **IScriptEngine**  que ya no tiene invocaciones activas CM-MED-001/002/003.  
2. **Métodos Huérfanos en Sandbox:**  En  **SandboxVerifier.cc** , eliminar EvaluateScript y AddTrustedSignature, junto con el vector miembro m\_trusted\_signatures CM-BAJ-004/014.  
3. **Fuentes Excluidos:**  Eliminar  **R\_Environment.cpp**  y  **Julia\_Environment.cpp** . Estos archivos, aunque presentes en el árbol de fuentes, fueron excluidos de  **CMakeLists.txt**  debido a incompatibilidades críticas con el  **Excel SDK**  bajo la arquitectura de procesos hijos CM-BAJ-011/012.

##### Consistencia en Exportaciones XLL

Para asegurar la integridad del registro de funciones en el framework XLL, se debe sincronizar el archivo de definiciones del proyecto:

* **Fix CM-MED-013:**  Incluir explícitamente la función  **RJ\_Q**  (NEVEN.q) en  **rj2xcl.def** . Actualmente, la función solo se exporta mediante \_\_declspec(dllexport), lo que representa un riesgo de mantenimiento por inconsistencia con el estándar de exportaciones del proyecto.

#### 3\. Estabilidad de Motores y Resolución Funcional

Basado en el "Roadmap de Líneas Futuras", se priorizan las correcciones que impactan la fiabilidad de los motores de lenguaje y la interoperabilidad reactiva.

1. **Corrección de Regresión en Julia 1.12:**  Resolver el bug de scope detectado en el módulo  **J.EDO**  para los TipoOutput 2-4. Este fallo es una regresión directa tras la actualización del motor Julia y afecta la resolución numérica de ecuaciones diferenciales.  
2. **Implementación de PLUTO.READ:**  Habilitar el flujo de datos bidireccional mediante el patrón  **PLUTO.READ**  (Pluto → Excel). Esto permitirá que los resultados procesados en notebooks reactivos retornen automáticamente a las celdas del host.  
3. **Estabilización de Viewer Professional:**  Finalizar la lógica del botón de guardado y activar la detección de  **hashes**  de contenido en  **WebView2**  para evitar recargas innecesarias que degradan el rendimiento visual.  
4. **Telemetría Local:**  Integrar de forma estable el  **CrashHandler**  para capturar  *health snapshots*  y reportes de excepciones SEH, facilitando el diagnóstico de fallos en despliegues distribuidos.

#### 4\. Validación Externa y Viabilidad del Proyecto

Para la consolidación académica de la tesis en la UCR y su viabilidad competitiva, se establecen los siguientes hitos de validación:

* **Benchmark de Rendimiento:**  Ejecución de una comparativa formal de latencia que contraste la arquitectura de  **Named Pipes \+ Protobuf**  de NEVEN frente a  **VBA**  nativo y  **xlwings** .  
* **Estudio de Usabilidad (UCR):**  Realización de pruebas controladas con usuarios reales en la Universidad de Costa Rica para validar la tesis de "democratización del análisis de datos".  
* **Comparativa de Mercado:**  Documentación técnica que posicione a NEVEN frente a alternativas comerciales como  **PyXLL**  y  **RExcel** .  
* **Declaración de Diseño:**  Formalizar en la documentación técnica que la limitación de plataforma (Windows-only) es una decisión de diseño dictada por la dependencia profunda de la  **XLL architecture**  y la  **Win32 API** .

#### 5\. Lista Maestra de Tareas Priorizadas (Master List)

Ordenadas por criticidad técnica y de seguridad.

* **Implementar aislamiento OS-Level (AppContainer):**  Migrar de filtros de patrones a restricciones de Kernel.  
* *Justificación:*  Mitigación del riesgo crítico de bypass de sandbox detectado en la auditoría de seguridad Doc 2.2.  
* **Remover cadena de código muerto RuntimeLoader → AutoLoader → GCMonitor:**  Eliminación de archivos y referencias en  **CMakeLists.txt** .  
* *Justificación:*  CM-MED-001/002/003 Código huérfano de alta severidad que compromete la integridad arquitectónica.  
* **Sincronizar rj2xcl.def con exportación RJ\_Q:**  Inclusión de la función de Quarto en el archivo de definiciones.  
* *Justificación:*  CM-MED-013 Prevención de inconsistencias en el framework XLL y riesgos de mantenimiento.  
* **Eliminar funciones con cuerpo vacío y comentarios residuales:**  Implementar o borrar  **RemoveUserButton**  y limpiar  **rj2xcl.cc** .  
* *Justificación:*  CM-BAJ-005/006/007 Higiene del código fuente y eliminación de ruido en el path crítico.  
* **Sanear métodos huérfanos en SandboxVerifier:**  Remover EvaluateScript y AddTrustedSignature.  
* *Justificación:*  CM-BAJ-004 Reducción de superficie de ataque y eliminación de lógica no consultada.  
* **Corregir bug de scope en Julia 1.12 para EDO:**  Arreglo en  **J.EDO**  (TipoOutput 2-4).  
* *Justificación:*  Corrección de una regresión funcional mayor en el motor de cálculo matemático.  
* **Remover archivos excluidos R\_Environment.cpp y Julia\_Environment.cpp:**  Mover a directorio legacy o eliminar.  
* *Justificación:*  CM-BAJ-011/012 Incompatibilidad insalvable con el  **Excel SDK**  bajo la arquitectura actual.  
* **Integración estable de CrashHandler:**  Activar telemetría de errores local.  
* *Justificación:*  Necesidad crítica de diagnóstico para la confiabilidad del sistema en producción.  
* **Implementar flujo bidireccional PLUTO.READ:**  Permitir lectura de Pluto desde Excel.  
* *Justificación:*  Cierre de brecha funcional identificada en el roadmap de interoperabilidad.  
* **Finalizar optimizaciones de Viewer Professional:**  Estabilizar guardado y validación de  **hashes** .  
* *Justificación:*  Mejora de UX y optimización de recursos en la visualización interactiva.  
1. **Ejecutar Benchmarks de Rendimiento:**  Comparativa contra  **VBA**  y  **xlwings** .  
* *Justificación:*  Validación cuantitativa de la eficiencia del protocolo de comunicación.  
1. **Documentar limitación Windows-only:**  Justificar dependencia de  **Win32 API**  y  **XLL** .  
* *Justificación:*  Transparencia académica sobre las restricciones de plataforma inherentes al diseño.  
1. **Realizar estudio de usabilidad (UCR):**  Pruebas de campo con usuarios universitarios.  
* *Justificación:*  Validación empírica de la propuesta de valor del proyecto para la defensa de tesis.

