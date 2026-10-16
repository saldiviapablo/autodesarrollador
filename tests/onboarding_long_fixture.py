"""Synthetic UX brief only; no customer text or real project is used."""
def objective():
    sections=[
        ('Identidad','Crear la landing de Estudio Horizonte, marca ficticia de excursiones. Jerarquía clara, títulos en español, sin inventar testimonios ni datos comerciales reales.'),
        ('Stack','HTML5 semántico, CSS3 y JavaScript sin dependencias. Entregar index.html, styles.css, script.js y README.md. Node ya instalado ejecuta verificadores; no instalar paquetes.'),
        ('Hero','Un único h1, resumen y CTA Ver planes que enlaza #planes. Usar el texto exacto: Explorá con calma. No reproducir este brief dentro de los archivos.'),
        ('Navegación','Header con enlaces internos #beneficios, #planes, #preguntas y #contacto. Deben existir destinos únicos y un enlace Saltar al contenido hacia el main.'),
        ('Beneficios','Tres beneficios con títulos y descripciones breves que expliquen el servicio sin promesas médicas ni cifras inventadas. Usar listas y encabezados con jerarquía correcta.'),
        ('Planes','Sección #planes con tres propuestas distinguibles, precio ilustrativo claramente marcado como ejemplo y CTA que llega al contacto. Nunca simular un pago real.'),
        ('Preguntas','Al menos tres preguntas. Usar details/summary accesibles o botones con aria-expanded coherente; no depender sólo del hover ni del color.'),
        ('Contacto','Formulario local con name, email y message, labels asociados y validación de vacío y formato. Tras envío válido mostrar confirmación local; cero requests de red y sin persistir datos.'),
        ('Diseño visual','Paleta de alto contraste, fondo claro, acento azul y espaciado consistente. Evitar texto sobre fondos de contraste dudoso. Tipografía del sistema, sin fuentes remotas.'),
        ('Responsive','CSS para 375px, 768px y 1440px, sin ancho fijo que desborde. Grillas flexibles, targets cómodos y párrafos legibles; no esconder contenido requerido en móvil.'),
        ('Teclado','Todos los enlaces y controles utilizables mediante teclado; foco visible y orden natural. Sin tabindex positivo, sin trampas de foco y sin controles falsos hechos con div.'),
        ('Accesibilidad','Documento lang=es, landmarks, alternativas de texto cuando hay imágenes, nombres accesibles y mensajes del formulario vinculados a los campos. No anular outline sin reemplazo.'),
        ('Movimiento','Respetar prefers-reduced-motion y evitar autoplay, parallax obligatorio o animaciones que impidan leer. Ninguna interacción esencial debe depender de movimiento.'),
        ('SEO','Title descriptivo y meta description propia, viewport correcto y HTML válido. No añadir trackers, scripts de terceros, cookies publicitarias ni secretos.'),
        ('Investigación web','Planificar consulta de documentación oficial pública en https://developer.mozilla.org/en-US/docs/Web/Accessibility antes de implementar. No navegar durante el planner. Usar el mecanismo gobernado existente después de aprobación.'),
        ('Pruebas','Definir pruebas inmutables Node sustantivas: landmarks y enlaces/destinos, copy del hero, campos/labels, comportamiento de validación local y opciones responsive/reduced-motion. Ningún PASS incondicional ni sólo existencia de archivos.'),
        ('Build','Verificación independiente de sintaxis JavaScript y referencias locales; sin deploy. Marcador explícito BUILD_PASS sólo tras checks exitosos. Todo comando debe terminar dentro de 60 segundos.'),
        ('README','Explicar apertura local, comandos de test/build y limitaciones del formulario de demostración. Incluir exactamente: áéíóú ñ ¿? € ° "comillas". No copiar este brief.'),
        ('Seguridad','Sólo editar outputs aprobados dentro de este sandbox; no infraestructura, credenciales, producción ni push. Los verificadores y criterios permanecen inmutables. No ChatGPT ni llamadas de red desde el producto.'),
        ('Cierre','Tests/build, artefactos, diff autorizado, estado, pendientes vacíos y Reviewer deben pasar el Completion Gate nativo. Mantener los presupuestos existentes, sin reinicios extra.')]
    lines=['# Brief UX/UI sintético — Horizonte','Objetivo: implementar una landing accesible y verificable en un sandbox descartable.']
    for i,(title,detail) in enumerate(sections,1):
        lines.extend(['',f'## {i}. {title}',detail,''])
        # Explicit review notes make a detailed multi-section source comparable
        # to the 17,520-byte incident without copying any customer content.
        for j in range(1,8):
            lines.extend([f'Revisión {i}.{j}: {detail}', ''])
    text='\n'.join(lines)
    # Preserve whole section notes; don't cut a UTF-8 code point or requirement.
    core='\n'.join(['# Criterios principales']+[f'{i}. {t}: {d}' for i,(t,d) in enumerate(sections,1)])
    tail=[]
    for line in text.splitlines():
        if len((core+'\n'+'\n'.join(tail+[line])).encode('utf-8'))>18000:break
        tail.append(line)
    return core+'\n'+'\n'.join(tail)+'\n'
