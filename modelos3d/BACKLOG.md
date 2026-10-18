# Colección de modelos 3D (MakerWorld) — trabajo nocturno

Reglas de todos los modelos:
- 2 colores, **una pieza por color** (sin AMS), encastre a presión. Juego TOL = 0.15 mm (provisorio hasta que Juan imprima la prueba).
- Base 3.2 mm, hueco 1.6 mm, encastre 2.0 mm (sobresale 0.4), bisel inferior escalonado 0.25 mm, grabado trasero 0.4 mm espejado.
- Paredes entre huecos ≥ 1.0 mm, trazos de encastre ≥ 1.2 mm de ancho. Sin piezas menores a 3 mm.
- Herramientas: `extru.py` (Stack/Canvas/text_arc/ellipse/closing, check, write_3mf), `cover.py` (shot/title).
- Usar `kit.build()` (incluye control de paredes finas `_control_paredes.png`: azul = pared de base < 0.9 mm, naranja = encastre < 0.85 mm). Letras con track ≥ 1.2. Formas comunes en `shapes.py` (paw, band, back_text, fit_cap, line). Huella: usar `paw()` (dedos 1.4×1.85, escala ≥ 0.7).
- Si el encastre con bisel no queda estanco, kit.build() lo rehace sin bisel (aviso en consola). extru.loops_of ahora quita vértices colineales.
- Piezas grandes (carteles): Canvas(..., res=0.04) para no quedarse sin memoria.
- kit.build() también exige que los huecos queden a ≥ 0.7 mm del borde exterior.
- Verificar SIEMPRE `check()` → estanca y orientada = True, y mirar la portada antes de darlo por hecho.
- Cada modelo en `out/coleccion/<nn>_<nombre>/`: plato1_base.3mf, plato2_encastres.3mf, portada.jpg, piezas.jpg, atras.jpg, 2 portadas con otras combinaciones de color, `makerworld.md` (título, descripción en español e inglés, etiquetas, ajustes de impresión, tiempo y gramos estimados).

## Pendientes (tomar de arriba hacia abajo, 2 por vuelta)
- [ ] 14 Imán de heladera hueso 'NO TE OLVIDES DEL PASEO' (hueco atrás para imán de 10×2 mm)
- [ ] 15 Señalador de libro con huellas (25×80 mm)
- [ ] 16 Nuevas ideas del nicho mascotas si se termina la lista (siempre 2D en capas, 2 colores)

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
- [x] Hoja de contacto 1080×1350 (out/coleccion/hoja_contacto_instagram.jpg) — regenerar al sumar modelos
- [x] Prueba de tolerancias (out/test_tolerancia)
- [x] Chapita hueso TOBY (out/chapita_hueso_TOBY)
- [x] Medalla redonda LOLA (out/medalla_LOLA)
- [x] Chapita huella MILO (out/huella_MILO)
