# Criterios principales
1. Identidad: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.
2. Stack: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.
3. Hero: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.
4. Navegación: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.
5. Beneficios: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.
6. Planes: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.
7. Preguntas: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.
8. Contacto: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.
9. Diseño visual: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.
10. Responsive: CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.
11. Teclado: Todos los enlaces y controles utilizables mediante teclado; foco visible y orden natural. Sin tabindex positivo, sin trampas de foco y sin controles falsos hechos con div.
12. Accesibilidad: Documento lang=es, landmarks, alternativas de texto cuando hay imágenes, nombres accesibles y mensajes del formulario vinculados a los campos. No anular outline sin reemplazo.
13. Movimiento: Respetar prefers-reduced-motion y evitar autoplay, parallax obligatorio o animaciones que impidan leer. Ninguna interacción esencial debe depender de movimiento.
14. SEO: Title descriptivo y meta description propia, viewport correcto y HTML válido. No añadir trackers, scripts de terceros, cookies publicitarias ni secretos.
15. Investigación web: Planificar consulta de documentación oficial pública en https://developer.mozilla.org/en-US/docs/Web/Accessibility antes de implementar. No navegar durante el planner. Usar el mecanismo gobernado existente después de aprobación.
16. Pruebas: Definir pruebas inmutables Node sustantivas: landmarks y enlaces/destinos, copy del hero, campos/labels, comportamiento de validación local y opciones responsive/reduced-motion. Ningún PASS incondicional ni sólo existencia de archivos.
17. Build: Verificación independiente de sintaxis JavaScript y referencias locales; sin deploy. Marcador explícito BUILD_PASS sólo tras checks exitosos. Todo comando debe terminar dentro de 60 segundos.
18. README: Explicar apertura local, comandos de test/build y limitaciones del formulario de demostración. Incluir exactamente: áéíóú ñ ¿? € ° "comillas". No copiar este brief.
19. Seguridad: Sólo editar outputs aprobados dentro de este sandbox; no infraestructura, credenciales, producción ni push. Los verificadores y criterios permanecen inmutables. No ChatGPT ni llamadas de red desde el producto.
20. Cierre: Tests/build, artefactos, diff autorizado, estado, pendientes vacíos y Reviewer deben pasar el Completion Gate nativo. Mantener los presupuestos existentes, sin reinicios extra.
# Brief UX/UI sintético — Horizonte
Objetivo: implementar una landing accesible y verificable en un sandbox descartable.

## 1. Identidad
Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.1: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.2: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.3: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.4: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.5: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.6: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.

Revisión 1.7: Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.


## 2. Stack
HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.1: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.2: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.3: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.4: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.5: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.6: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.

Revisión 2.7: HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.


## 3. Hero
Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.1: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.2: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.3: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.4: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.5: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.6: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.

Revisión 3.7: Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.


## 4. Navegación
Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.1: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.2: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.3: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.4: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.5: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.6: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.

Revisión 4.7: Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.


## 5. Beneficios
Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.1: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.2: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.3: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.4: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.5: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.6: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.

Revisión 5.7: Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.


## 6. Planes
Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.1: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.2: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.3: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.4: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.5: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.6: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.

Revisión 6.7: Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.


## 7. Preguntas
Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.1: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.2: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.3: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.4: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.5: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.6: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.

Revisión 7.7: Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.


## 8. Contacto
Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.1: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.2: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.3: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.4: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.5: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.6: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.

Revisión 8.7: Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.


## 9. Diseño visual
Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.1: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.2: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.3: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.4: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.5: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.6: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.

Revisión 9.7: Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.


## 10. Responsive
CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.

Revisión 10.1: CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.

Revisión 10.2: CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.

Revisión 10.3: CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.

Revisión 10.4: CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.

Revisión 10.5: CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.

