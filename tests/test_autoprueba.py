from firmador_masivo.autoprueba import autoprueba


def test_autoprueba_termina_en_cero():
    assert autoprueba() == 0
