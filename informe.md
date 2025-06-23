---
lang: es
title: "Informe del Proyecto CyberMind: SVAIA SmartTrack"
author: Rafael Expósito Muñoz, Alejandro Galán Rita, Javier Martín Jurado y Jesús Martínez Ortiz
date: 2025-06-23
geometry: margin=2cm
numbersections: true
colorlinks: true
linkcolor: black
toc: true
header-includes:
  - \usepackage{enumitem}
  - \usepackage{forest}
  - \usepackage{amsmath}
  - \usepackage{lastpage}
  - \DeclareMathOperator*{\argmax}{arg\,max}
  - \setlistdepth{20}
  - \renewlist{itemize}{itemize}{20}
  - \renewlist{enumerate}{enumerate}{20}
  - \setlist[itemize]{label=$\cdot$}
  - \setlist[itemize,1]{label=\textbullet}
  - \setlist[itemize,2]{label=--}
  - \setlist[itemize,3]{label=*}
  - \usepackage{fancyhdr}
  - \pagestyle{fancy}
  - \fancyhead{}
  - \fancyfoot{}
  - "\\renewcommand{\\headrulewidth}{0.4pt}"
  - "\\renewcommand{\\footrulewidth}{0.4pt}"
  - \fancyhead[R]{Proyecto CyberMind}
  - \fancyhead[L]{Ingeniería del Software Seguro - CIA Málaga}
  - \fancyfoot[C]{\thepage \hspace{1pt} de \pageref*{LastPage}}
  - \fancyfoot[R]{INFISS20250623}
---
<!--Informe realizado en Pandoc Markdown-->
<!--Compilar con: pandoc informe.md -o informe.pdf-->

\pagebreak

# Introducción

El proyecto CyberMind consiste en el desarrollo de la base del **Sistema de soporte para Vulnerabilidades y Amenazas basado en Inteligencia Artificial (SVAIA)** con el añadido **SmartTrack**, un sistema de seguimiento, generación de reportes y notificaciones de amenazas. De esta forma, la aplicación completa permite gestionar un proyecto, recibir asistencia personalizada con inteligencia artificial, analizar dependencias, generar reportes periódicos, y enviar notificaciones. Con esta aplicación, un equipo de *software* desarrollo podrá mantenerse al día en los cambios en su sistema, las vulnerabilidades a las que se enfrentan y las diferentes formas de mitigarlas.

# Miembros del Equipo

## Rafael Expósito Muñoz

Rafael ha actuado como **analista de requisitos**, **líder de proyecto ágil**, **arquitecto de *software*** y **desarrollador *backend* de microservicios**. Durante todas las iteraciones del proyecto ha tomado los roles mencionados al establecer las metas semanales, diseñar la arquitectura general del sistema mediante el análisis de los requisitos y su materialización en objetivos concretos y abarcables, y la programación de los microservicios en el *backend*. En general, ha hecho posible las conexiones, diseño seguro y refactorización del sistema.

## Alejandro Galán Rita

Alejandro ha actuado como **diseñador de APIs**, **ingeniero de seguridad de aplicaciones**, **ingeniero DevOps** y **administrador de bases de datos**. Durante todas las iteraciones del proyecto ha tomado los roles mencionados al establecer los contratos de los microservicios, analizar la seguridad de los componentes *software* diseñados, desarrollar de forma segura los componentes, gestión de la construcción, el despliegue y la automatización, y el diseño de la estructura de la base de datos. En general, ha hecho posible el despliegue y la separación de privilegios y responsabilidades de los microservicios.  

## Javier Martín Jurado

Javier ha actuado como **desarrollador *frontend***, **ingeniero de observabilidad** e **ingeniero de pruebas de seguridad**. Durante todas las iteraciones del proyecto ha tomado los roles mencionados al desarrollar la experiencia e interfaz de usuario, coordinar los eventos producidos por los microservicios, y ejecutar pruebas para encontrar vulnerabilidades en el sistema. En general, ha hecho posible que la aplicación web mantenga un estilo consistente y una seguridad adecuada desde la experiencia del usuario.

## Jesús Martínez Ortiz

Jesús ha actuado como **desarrollador *frontend***, ***QA Tester*** y **administrador de identidad y acceso**. Durante todas las iteraciones del proyecto ha tomado los roles mencionados al establecer las comunicaciones entre el cliente y los microservicios, diseñar métodos de prueba y *debugging* manuales para demostrar la eficacia y seguridad de los *endpoints*, y gestionar el control de acceso y creación de usuarios. En general, ha hecho posible la gestión de los envíos de información a través de JSON de forma segura y la autenticación de los usuarios.

# Arquitectura



\pagebreak

# Componentes



\pagebreak

# Técnicas



\pagebreak

# Consideraciones Finales



\pagebreak

# Anexo I: Documentación