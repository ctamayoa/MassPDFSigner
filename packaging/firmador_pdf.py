"""Punto de entrada para PyInstaller (evita imports relativos en el script principal)."""
import sys

if __name__ == "__main__":
    if "--autoprueba" in sys.argv:
        from firmador_masivo.autoprueba import autoprueba
        sys.exit(autoprueba())
    from firmador_masivo.gui import main
    main()
