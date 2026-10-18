# Colección de modelos 3D (MakerWorld) — trabajo nocturno

Reglas de todos los modelos:
- 2 colores, **una pieza por color** (sin AMS), encastre a presión. Juego TOL = 0.15 mm (provisorio hasta que Juan imprima la prueba).
- Base 3.2 mm, hueco 1.6 mm, encastre 2.0 mm (sobresale 0.4), bisel inferior escalonado 0.25 mm, grabado trasero 0.4 mm espejado.
- Paredes entre huecos ≥ 1.0 mm, trazos de encastre ≥ 1.2 mm de ancho. Sin piezas menores a 3 mm.
- Herramientas: `extru.py` (Stack/Canvas/text_arc/ellipse/closing, check, write_3mf), `cover.py` (shot/title).
- Usar `kit.build()` (incluye control de paredes finas `_control_paredes.png`: azul = pared de base < 0.9 mm, naranja = encastre < 0.85 mm). Letras con track ≥ 1.2. Formas comunes en `shapes.py` (paw, band, back_text, fit_cap, line). Huella: usar `paw()` (dedos 1.4×1.85, escala ≥ 0.7).
- Si el encastre con bisel no queda estanco, kit.build() lo rehace sin bisel (aviso en consola). extru.loops_of ahora quita vértices colineales.
- Piezas grandes (carteles): Canvas(..., res=0.04) para no quedarse sin memoria.
- build(base_h=..., back_d=...) permite piezas más gruesas y huecos traseros profundos (imanes). earcut.KEEP_COLLINEAR=True evita uniones en T.
- Dejar ≥ 3 mm entre la pieza y el borde del Canvas si se usa closing() (si no, aparecen muescas).
- kit.build() también exige que los huecos queden a ≥ 0.7 mm del borde exterior.
- Verificar SIEMPRE `check()` → estanca y orientada = True, y mirar la portada antes de darlo por hecho.
- Cada modelo en `out/coleccion/<nn>_<nombre>/`: plato1_base.3mf, plato2_encastres.3mf, portada.jpg, piezas.jpg, atras.jpg, 2 portadas con otras combinaciones de color, `makerworld.md` (título, descripción en español e inglés, etiquetas, ajustes de impresión, tiempo y gramos estimados).

## Pendientes (tomar de arriba hacia abajo, 2 por vuelta)
- [ ] 22 Cartel humor 'AQUÍ VIVE UN GATO… Y SUS EMPLEADOS' 120×60
- [ ] 23 Plaquita para el plato 'COMIDA DE ____' 70×22 con hueso (se pega con cinta doble faz)
- [ ] 24 Nuevas ideas del nicho mascotas si se termina la lista (siempre 2D en capas, 2 colores)

## Hechos
- [x] 01 Corazón LUNA (out/coleccion/01_corazon)
- [x] 02 Hueso premium ROCKY (out/coleccion/02_hueso_premium)
- [x] 03 Medalla redonda LOLA rehecha (out/coleccion/03_medalla_redonda) — reemplaza out/medalla_LOLA
- [x] 04 Chapita huella MILO rehecha (out/coleccion/04_chapita_huella) — reemplaza out/huella_MILO
- [x] 05 Cabeza de gato SIMBA (out/coleccion/05_cabeza_gato)
- [x] 06 Placa K9 MAX (out/coleccion/06_placa_k9) — encastre sin bisel (fallback)
- [x] 07 Llavero huella con corazón (out/coleccion/07_llavero_huella)
- [x] 08 Cartel de cucha CASA DE ROCKY 120×40 (out/coleccion/08_cartel_cucha)
- [x] 09 Cartel ¡Cuidado! Perro cariñoso 120×60 (out/coleccion/09_cartel_perro_carinoso)
- [x] 10 Medalla estrella COCO (out/coleccion/10_medalla_estrella)
- [x] 11 Chapita hexágono geométrico NALA (out/coleccion/11_hexagono_geometrico)
- [x] 12 Medalla corazón KIRA (out/coleccion/12_medalla_corazon)
- [x] 13 Posavasos huella 90 mm (out/coleccion/13_posavasos_huella)
- [x] 14 Imán hueso 'No te olvides del paseo' con 2 huecos para imán 10×2 (out/coleccion/14_iman_hueso_paseo) — base 4.4 mm
- [x] 15 Señalador con huellas 26×82 (out/coleccion/15_senalador_huellas) — base 2.4 mm
- [x] 16 Escudo de club C.A. TOBY (out/coleccion/16_escudo_club)
- [x] 17 Llavero ADOPTÁ (out/coleccion/17_llavero_adopta)
- [x] 18 Cartel 'Acá no se hace caca' 120×80 con perro (out/coleccion/18_cartel_caca) — función sitting_dog en m18_19.py
- [x] 19 Imán 'Mi perro es mi terapia' 96×45 (out/coleccion/19_iman_terapia)
- [x] 20 Chapita médica BRUNO (out/coleccion/20_chapita_medica)
- [x] 21 Medalla gato MICHI (out/coleccion/21_medalla_gato) — función sitting_cat en m20_21.py
- [x] Hoja de contacto 1080×1350 (out/coleccion/hoja_contacto_instagram.jpg) — regenerar al sumar modelos
- [x] Prueba de tolerancias (out/test_tolerancia)
- [x] Chapita hueso TOBY (out/chapita_hueso_TOBY)
- [x] Medalla redonda LOLA (out/medalla_LOLA)
- [x] Chapita huella MILO (out/huella_MILO)
