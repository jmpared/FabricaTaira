# Colección de modelos 3D (MakerWorld) — trabajo nocturno

Reglas de todos los modelos:
- 2 colores, **una pieza por color** (sin AMS), encastre a presión. Juego TOL = 0.15 mm (provisorio hasta que Juan imprima la prueba).
- Base 3.2 mm, hueco 1.6 mm, encastre 2.0 mm (sobresale 0.4), bisel inferior escalonado 0.25 mm, grabado trasero 0.4 mm espejado.
- Paredes entre huecos ≥ 1.0 mm, trazos de encastre ≥ 1.2 mm de ancho. Sin piezas menores a 3 mm.
- Herramientas: `extru.py` (Stack/Canvas/text_arc/ellipse/closing, check, write_3mf), `cover.py` (shot/title).
- Usar `kit.build()` (incluye control de paredes finas `_control_paredes.png`: azul = pared de base < 0.9 mm, naranja = encastre < 0.85 mm). Letras con track ≥ 1.2. Formas comunes en `shapes.py` (paw, band, back_text, fit_cap, line). Huella: usar `paw()` (dedos 1.4×1.85, escala ≥ 0.7).
- kit.build() también exige que los huecos queden a ≥ 0.7 mm del borde exterior.
- Verificar SIEMPRE `check()` → estanca y orientada = True, y mirar la portada antes de darlo por hecho.
- Cada modelo en `out/coleccion/<nn>_<nombre>/`: plato1_base.3mf, plato2_encastres.3mf, portada.jpg, piezas.jpg, atras.jpg, 2 portadas con otras combinaciones de color, `makerworld.md` (título, descripción en español e inglés, etiquetas, ajustes de impresión, tiempo y gramos estimados).

## Pendientes (tomar de arriba hacia abajo, 2 por vuelta)
- [ ] 04 Escudo / placa de policía "K9" con nombre (humor)
- [ ] 05 Llavero huella chico para dueños (30 mm, "TE QUIERO" o nombre)
- [ ] 06 Cartel de cucha "CASA DE ____" 120×40 mm con huesitos en las puntas
- [ ] 07 Cartel "CUIDADO: PERRO CARIÑOSO" (humor) 120×60
- [ ] 08 Medalla redonda variante estrella / variante corazón central
- [ ] 09 Chapita hexágono moderno con huella geométrica
- [ ] 10 Hoja de contacto con todas las portadas de la colección (imagen para Instagram de TAIRA)
- [ ] 11 Nuevas ideas del nicho mascotas si se termina la lista (siempre 2D en capas, 2 colores)

## Hechos
- [x] 01 Corazón LUNA (out/coleccion/01_corazon)
- [x] 02 Hueso premium ROCKY (out/coleccion/02_hueso_premium)
- [x] 03 Medalla redonda LOLA rehecha (out/coleccion/03_medalla_redonda) — reemplaza out/medalla_LOLA
- [x] 04 Chapita huella MILO rehecha (out/coleccion/04_chapita_huella) — reemplaza out/huella_MILO
- [x] 05 Cabeza de gato SIMBA (out/coleccion/05_cabeza_gato)
- [x] Prueba de tolerancias (out/test_tolerancia)
- [x] Chapita hueso TOBY (out/chapita_hueso_TOBY)
- [x] Medalla redonda LOLA (out/medalla_LOLA)
- [x] Chapita huella MILO (out/huella_MILO)
