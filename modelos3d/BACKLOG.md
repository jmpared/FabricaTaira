# Colección de modelos 3D (MakerWorld) — trabajo nocturno

Reglas de todos los modelos:
- 2 colores, **una pieza por color** (sin AMS), encastre a presión. Juego TOL = 0.15 mm (provisorio hasta que Juan imprima la prueba).
- Base 3.2 mm, hueco 1.6 mm, encastre 2.0 mm (sobresale 0.4), bisel inferior escalonado 0.25 mm, grabado trasero 0.4 mm espejado.
- Paredes entre huecos ≥ 1.0 mm, trazos de encastre ≥ 1.2 mm de ancho. Sin piezas menores a 3 mm.
- Herramientas: `extru.py` (Stack/Canvas/text_arc/ellipse/closing, check, write_3mf), `cover.py` (shot/title).
- Verificar SIEMPRE `check()` → estanca y orientada = True, y mirar la portada antes de darlo por hecho.
- Cada modelo en `out/coleccion/<nn>_<nombre>/`: plato1_base.3mf, plato2_encastres.3mf, portada.jpg, piezas.jpg, atras.jpg, 2 portadas con otras combinaciones de color, `makerworld.md` (título, descripción en español e inglés, etiquetas, ajustes de impresión, tiempo y gramos estimados).

## Pendientes (tomar de arriba hacia abajo, 2 por vuelta)
- [ ] 01 Corazón con huella chica y nombre (corazón 36 mm, aro de borde)
- [ ] 02 Hueso premium (borde encastrado + nombre + huesito decorativo)
- [ ] 03 Cabeza de gato (con orejas y bigotes encastrados, nombre)
- [ ] 04 Escudo / placa de policía "K9" con nombre (humor)
- [ ] 05 Llavero huella chico para dueños (30 mm, "TE QUIERO" o nombre)
- [ ] 06 Cartel de cucha "CASA DE ____" 120×40 mm con huesitos en las puntas
- [ ] 07 Cartel "CUIDADO: PERRO CARIÑOSO" (humor) 120×60
- [ ] 08 Medalla redonda variante estrella / variante corazón central
- [ ] 09 Chapita hexágono moderno con huella geométrica
- [ ] 10 Hoja de contacto con todas las portadas de la colección (imagen para Instagram de TAIRA)
- [ ] 11 Nuevas ideas del nicho mascotas si se termina la lista (siempre 2D en capas, 2 colores)

## Hechos
- [x] Prueba de tolerancias (out/test_tolerancia)
- [x] Chapita hueso TOBY (out/chapita_hueso_TOBY)
- [x] Medalla redonda LOLA (out/medalla_LOLA)
- [x] Chapita huella MILO (out/huella_MILO)
