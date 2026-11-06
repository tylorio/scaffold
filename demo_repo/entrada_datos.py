def leerNum(t):
    try:
        return int(t)
    except ValueError:
        print('no es numero')
        return 0


def div(a,b):
    try:
        r=a/b
    except ZeroDivisionError:
        r=None
    return r


def abrir(ruta):
    f=None
    try:
        f=open(ruta)
        return f.read()
    except FileNotFoundError:
        return ""
    finally:
        if f:
            f.close()


def checkEdad(e):
    if e<0:
        raise ValueError("edad mala")
    return e
