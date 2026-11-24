"""Plan de música (Kevin MacLeod, CC BY 4.0). Las ganancias normalizan las pistas (LUFS medidos) para que quede ~-27 LUFS bajo la voz."""
MUSICA = [
    # misterio del sobre: cuerdas graves, casi marcha fúnebre
    dict(archivo="recursos/musica/macleod-oppressive_gloom.mp3", desde="frio", off=0.0, hasta="titulo", off_fin=-4.2, ss=0, gain=-9, fi=3.0, fo=2.0),
    # irrumpe la épica con el título y acompaña la orden del capitán
    dict(archivo="recursos/musica/macleod-crusade.mp3", desde="titulo", off=0.2, hasta="orden", off_fin=0.0, ss=0, gain=-15, fi=0.8, fo=3.5),
    # cama marcial del informe de campo (tambores)
    dict(archivo="recursos/musica/macleod-undaunted.mp3", desde="acto2", off=0.2, hasta="jj5", off_fin=0.0, ss=8, gain=-11, fi=2.5, fo=3.0),
    # clímax de la prueba de fuego (el coral de trombones coincide con «TEST COMPLETO»)
    dict(archivo="recursos/musica/macleod-crusade.mp3", desde="prueba", off=-0.8, hasta="prueba", off_fin=1.0, ss=117, gain=-9, fi=2.0, fo=2.5),
    # el regreso: orquesta solemne bajo el diálogo
    dict(archivo="recursos/musica/macleod-noble_race.mp3", desde="acto3", off=0.0, hasta="regreso", off_fin=0.0, ss=34, gain=-6, fi=2.0, fo=2.0),
    # cierre heroico y créditos
    dict(archivo="recursos/musica/macleod-heroic_age.mp3", desde="fin", off=0.2, hasta="fin", off_fin=0.0, ss=0, gain=-6, fi=0.6, fo=5.0),
]
CREDITOS = [
    ("MÚSICA", "Kevin MacLeod · incompetech.com"),
    ("", "«Oppressive Gloom» · «Crusade» · «Undaunted»"),
    ("", "«Noble Race» · «Heroic Age»  ·  CC BY 4.0"),
    ("FOTOS Y CAPTURAS", "del propio montaje y de la app"),
]
