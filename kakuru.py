# kakuru.py

# ============================================
# KAKURO CSP
# Backtracking + Forward Checking + MRV
# ============================================

from functools import lru_cache
from itertools import combinations, permutations
import os
import re
import time

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

SIZE = 9
DIGITS = set(range(1, 10))
CELL_WIDTH = 9
VERBOSE = False
nodos = 0
backtracks = 0


class TableroInvalido(ValueError):
    """Error controlado para mostrar por que un archivo no se puede resolver."""


# ============================================
# BANNER
# ============================================

def print_banner():
    console.clear()
    contenido = (
        "[bold bright_magenta]KAKURO CSP[/bold bright_magenta]\n\n"
        "[white]Solucionador optimizado con:[/white]\n"
        "[green]- Backtracking[/green]  [yellow]- Forward Checking[/yellow]\n"
        "[magenta]- Heuristica MRV[/magenta]  [cyan]- Propagacion por combinaciones[/cyan]\n\n"
        "[white]Presiona Ctrl+C para salir.[/white]"
    )

    console.print(
        Panel.fit(
            contenido,
            border_style="bright_magenta",
            padding=(1, 4),
            title="[bold yellow]BIENVENIDO AL JUEGO KAKURO[/bold yellow]",
            style="on black",
        ),
        justify="center",
    )


# ============================================
# MENU
# ============================================

def menu_principal():
    console.print()
    console.rule("[bold red]ARCHIVOS DISPONIBLES - DIFICIL[/bold red]")

    carpeta = "test/dificil"

    try:
        archivos = [f for f in sorted(os.listdir(carpeta)) if f.endswith(".txt")]
    except OSError as exc:
        raise TableroInvalido(f"No se pudo abrir la carpeta '{carpeta}': {exc}") from exc

    if not archivos:
        raise TableroInvalido("No se encontraron archivos .txt en la carpeta seleccionada.")

    for i, nombre in enumerate(archivos, start=1):
        console.print(f"[green]{i}.[/green] {nombre}")

    eleccion = console.input(f"\n[bold cyan]Seleccione archivo (1-{len(archivos)}):[/bold cyan] ")

    try:
        idx = int(eleccion)
        if 1 <= idx <= len(archivos):
            return os.path.join(carpeta, archivos[idx - 1])
    except ValueError:
        pass

    raise TableroInvalido("Opcion invalida en el menu de archivos.")


# ============================================
# ERRORES
# ============================================

def mostrar_error_rojo(titulo, detalle):
    console.print()
    console.print(
        Panel(
            f"[bold red]{titulo}[/bold red]\n\n[white]{detalle}[/white]",
            border_style="red",
            title="[bold white on red] ERROR [/]",
            padding=(1, 2),
        )
    )


# ============================================
# LEER TABLERO
# ============================================

def cargar_tablero(nombre_archivo):
    tablero = []

    try:
        with open(nombre_archivo, "r", encoding="utf-8-sig") as archivo:
            for numero_linea, linea in enumerate(archivo, start=1):
                limpia = linea.strip()
                if not limpia:
                    raise TableroInvalido(f"La fila {numero_linea} esta vacia.")

                fila = [celda.strip() for celda in limpia.split(",")]
                if len(fila) != SIZE:
                    raise TableroInvalido(
                        f"La fila {numero_linea} tiene {len(fila)} celdas; debe tener {SIZE}."
                    )

                tablero.append(fila)
    except FileNotFoundError as exc:
        raise TableroInvalido(f"No existe el archivo: {nombre_archivo}") from exc
    except OSError as exc:
        raise TableroInvalido(f"No se pudo leer el archivo: {exc}") from exc

    if len(tablero) != SIZE:
        raise TableroInvalido(f"El tablero tiene {len(tablero)} filas; debe tener {SIZE}.")

    validar_tablero(tablero)
    return tablero


def validar_tablero(tablero):
    if len(tablero) != SIZE:
        raise TableroInvalido(f"El tablero tiene {len(tablero)} filas; debe tener {SIZE}.")

    for fila in range(SIZE):
        if len(tablero[fila]) != SIZE:
            raise TableroInvalido(
                f"La fila {fila + 1} tiene {len(tablero[fila])} celdas; debe tener {SIZE}."
            )

        for columna in range(SIZE):
            celda = tablero[fila][columna]
            ubicacion = f"fila {fila + 1}, columna {columna + 1}"

            if celda == "":
                raise TableroInvalido(f"Celda vacia en {ubicacion}.")

            if celda == "N":
                continue

            if celda.startswith("C"):
                obtener_pistas(celda, ubicacion)
                continue

            if not re.fullmatch(r"[1-9]+", celda):
                raise TableroInvalido(
                    f"Celda invalida en {ubicacion}: '{celda}'. Use N, pistas C..., o digitos 1-9."
                )

            if len(set(celda)) != len(celda):
                raise TableroInvalido(f"Dominio repetido en {ubicacion}: '{celda}'.")


# ============================================
# CREAR VARIABLES
# ============================================

def crear_variables(tablero):
    dominios = {}

    for f in range(SIZE):
        for c in range(SIZE):
            celda = tablero[f][c]
            if celda == "N" or celda.startswith("C"):
                continue
            dominios[f"{f},{c}"] = {int(d) for d in celda}

    if not dominios:
        raise TableroInvalido("El tablero no contiene celdas jugables.")

    return dominios


# ============================================
# EXTRAER PISTAS
# ============================================

def obtener_pistas(celda, ubicacion="celda"):
    if celda == "N" or not celda.startswith("C"):
        return None, None

    contenido = celda[1:]
    if not contenido:
        raise TableroInvalido(f"Pista sin valor en {ubicacion}.")

    partes = contenido.split("\\")
    if len(partes) > 2:
        raise TableroInvalido(f"Pista invalida en {ubicacion}: '{celda}'.")

    def parse_valor(parte, orientacion=None):
        if parte in ("", "N"):
            return None

        if parte.startswith("CV"):
            orientacion = "V"
            parte = parte[2:]
        elif parte.startswith("CH"):
            orientacion = "H"
            parte = parte[2:]
        elif parte.startswith("V"):
            orientacion = "V"
            parte = parte[1:]
        elif parte.startswith("H"):
            orientacion = "H"
            parte = parte[1:]
        elif parte.startswith("C"):
            parte = parte[1:]

        if not parte.isdigit():
            raise TableroInvalido(f"Pista invalida en {ubicacion}: '{celda}'.")

        valor = int(parte)
        if not 1 <= valor <= 45:
            raise TableroInvalido(f"Suma fuera de rango en {ubicacion}: {valor}.")

        return orientacion, valor

    horizontal = None
    vertical = None

    if len(partes) == 1:
        orientacion, valor = parse_valor(partes[0])
        if orientacion == "V":
            vertical = valor
        else:
            horizontal = valor
    else:
        _, vertical = parse_valor(partes[0], "V")
        _, horizontal = parse_valor(partes[1], "H")

    return horizontal, vertical


# ============================================
# CREAR GRUPOS
# ============================================

def crear_grupos(tablero):
    grupos = []

    for fila in range(SIZE):
        for columna in range(SIZE):
            celda = tablero[fila][columna]
            if not celda.startswith("C"):
                continue

            suma_h, suma_v = obtener_pistas(celda, f"fila {fila + 1}, columna {columna + 1}")

            if suma_h is not None:
                variables = []
                c = columna + 1
                while c < SIZE and tablero[fila][c] != "N" and not tablero[fila][c].startswith("C"):
                    variables.append(f"{fila},{c}")
                    c += 1
                if variables:
                    grupos.append(crear_grupo("H", suma_h, variables, (fila, columna)))

            if suma_v is not None:
                variables = []
                f = fila + 1
                while f < SIZE and tablero[f][columna] != "N" and not tablero[f][columna].startswith("C"):
                    variables.append(f"{f},{columna}")
                    f += 1
                if variables:
                    grupos.append(crear_grupo("V", suma_v, variables, (fila, columna)))

    if not grupos:
        raise TableroInvalido("No se encontraron pistas C... que formen grupos.")

    variables_en_grupos = {var for grupo in grupos for var in grupo["variables"]}
    variables_tablero = {
        f"{f},{c}"
        for f in range(SIZE)
        for c in range(SIZE)
        if tablero[f][c] != "N" and not tablero[f][c].startswith("C")
    }
    sin_pista = variables_tablero - variables_en_grupos
    if sin_pista:
        var = sorted(sin_pista)[0]
        f, c = map(int, var.split(","))
        raise TableroInvalido(f"La celda jugable en fila {f + 1}, columna {c + 1} no pertenece a ninguna pista.")

    return grupos


def crear_grupo(tipo, suma, variables, origen):
    fila, columna = origen
    descripcion = f"pista {tipo} en fila {fila + 1}, columna {columna + 1}"

    if not variables:
        raise TableroInvalido(f"La {descripcion} no tiene celdas jugables.")

    if len(variables) > 9:
        raise TableroInvalido(f"La {descripcion} tiene mas de 9 celdas.")

    if not combinaciones_validas(len(variables), suma):
        raise TableroInvalido(
            f"La {descripcion} pide suma {suma} con {len(variables)} celdas, algo imposible en Kakuro."
        )

    return {
        "tipo": tipo,
        "suma": suma,
        "variables": variables,
        "origen": origen,
        "tuplas": combinaciones_validas(len(variables), suma),
    }


def indexar_grupos(grupos):
    indice = {}
    for grupo in grupos:
        for variable in grupo["variables"]:
            indice.setdefault(variable, []).append(grupo)
    return indice


@lru_cache(maxsize=None)
def combinaciones_validas(longitud, suma):
    tuplas = []
    for combo in combinations(range(1, 10), longitud):
        if sum(combo) == suma:
            tuplas.extend(permutations(combo))
    return tuple(tuplas)


# ============================================
# MOSTRAR TABLERO
# ============================================

def mostrar(tablero, dominios, titulo="Estado actual del Kakuro", resaltada=None, estado=None):
    console.print()
    tabla = Table(
        title=f"[bold bright_magenta]{titulo}[/bold bright_magenta]",
        box=box.SQUARE,
        show_lines=True,
        header_style="bold bright_yellow",
        border_style="red",
        padding=(0, 1),
        expand=False,
    )

    tabla.add_column("", justify="center", style="bold bright_yellow", width=3)
    for col in "ABCDEFGHI":
        tabla.add_column(col, justify="center", width=CELL_WIDTH, no_wrap=True)

    for fila in range(SIZE):
        celdas = [f"[bold bright_yellow]{fila + 1}[/]"]
        for columna in range(SIZE):
            celda = tablero[fila][columna]
            celdas.append(renderizar_celda(celda, dominios, fila, columna, resaltada, estado))
        tabla.add_row(*celdas)

    console.print(Panel(tabla, border_style="bright_magenta", style="on black"), justify="center")


def renderizar_celda(celda, dominios, fila, columna, resaltada=None, estado=None):
    es_resaltada = resaltada == f"{fila},{columna}"

    if celda == "N":
        return Text(" " * CELL_WIDTH, style="on grey15")

    if celda.startswith("C"):
        h, v = obtener_pistas(celda)
        texto = Text(justify="center")
        if v is not None:
            texto.append(f"V{v}", style="bold cyan")
        else:
            texto.append("  ", style="bold cyan")
        texto.append("\\", style="white")
        if h is not None:
            texto.append(f"H{h}", style="bold yellow")
        texto.stylize("on black") 
        return texto

    nombre = f"{fila},{columna}"
    dominio = dominios[nombre]

    if len(dominio) == 1:
        estilo = "bold white on rgb(15,78,55)"
        if es_resaltada:
            estilo = "bold black on yellow" if estado == "ok" else "bold white on red"
        return Text(str(next(iter(dominio))).center(CELL_WIDTH), style=estilo)

    texto = "".join(str(x) for x in sorted(dominio))
    if len(texto) > CELL_WIDTH:
        texto = texto[: CELL_WIDTH - 1] + "+"
    estilo = "bold red on grey7"
    if es_resaltada:
        estilo = "bold black on yellow" if estado == "ok" else "bold white on red"
    return Text(texto.center(CELL_WIDTH), style=estilo)


def mostrar_grupos(grupos):
    tabla = Table(title="Grupos", show_header=True, header_style="bold magenta", box=box.MINIMAL)
    tabla.add_column("Tipo", justify="center", width=4)
    tabla.add_column("Suma", justify="center", width=6)
    tabla.add_column("Origen", justify="center", width=8)
    tabla.add_column("Celdas", justify="center", width=6)
    tabla.add_column("Opciones", justify="center", width=8)

    for g in grupos:
        origen = f"{g['origen'][0] + 1},{g['origen'][1] + 1}"
        tabla.add_row(
            f"[bold cyan]{g['tipo']}[/]",
            f"[bold yellow]{g['suma']}[/]",
            f"[green]{origen}[/]",
            f"[white]{len(g['variables'])}[/]",
            f"[magenta]{len(g['tuplas'])}[/]",
        )

    console.print(Panel(tabla, border_style="magenta", style="on black"))


def nombre_celda(variable):
    fila, columna = map(int, variable.split(","))
    return f"{chr(ord('A') + columna)}{fila + 1}"


def contar_dominios(dominios):
    return sum(len(dominio) for dominio in dominios.values())


def describir_grupos_variable(variable, grupos_por_variable):
    partes = []
    for grupo in grupos_por_variable.get(variable, []):
        direccion = "Vertical" if grupo["tipo"] == "V" else "Horizontal"
        partes.append(f"{direccion}: suma {grupo['suma']} con {len(grupo['variables'])} celdas")
    return "\n".join(partes) if partes else "Esta celda no pertenece a ningun grupo"


def mostrar_paso(tablero, dominios, variable, valor, nivel, estado, detalle, grupos_por_variable):
    color = "green" if estado == "ok" else "red"
    etiqueta = "SI FUNCIONA" if estado == "ok" else "NO FUNCIONA"
    fila, columna = map(int, variable.split(","))

    tabla = Table.grid(padding=(0, 2))
    tabla.add_column(style="bold cyan", no_wrap=True)
    tabla.add_column(style="white")
    tabla.add_row("Profundidad", str(nivel))
    tabla.add_row("Celda", f"{nombre_celda(variable)}  (fila {fila + 1}, columna {columna + 1})")
    tabla.add_row("Valor que se probo", str(valor))
    tabla.add_row("Grupos afectados", describir_grupos_variable(variable, grupos_por_variable))
    tabla.add_row("Resultado", f"[bold {color}]{etiqueta}[/bold {color}]")
    tabla.add_row("Explicacion", detalle)

    console.print()
    console.print(
        Panel(
            tabla,
            title=f"[bold {color}]Paso de busqueda explicado[/bold {color}]",
            border_style=color,
            padding=(1, 2),
        )
    )
    mostrar(
        tablero,
        dominios,
        f"Profundidad {nivel} - Se prueba {nombre_celda(variable)} = {valor} - {etiqueta}",
        resaltada=variable,
        estado=estado,
    )


# ============================================
# CONSISTENCIA Y PROPAGACION
# ============================================

def filtrar_tuplas(grupo, dominios):
    variables = grupo["variables"]
    validas = []

    for tupla in grupo["tuplas"]:
        for posicion, variable in enumerate(variables):
            if tupla[posicion] not in dominios[variable]:
                break
        else:
            validas.append(tupla)

    return validas


def propagar(grupos, dominios):
    cambio = True

    while cambio:
        cambio = False

        for grupo in grupos:
            variables = grupo["variables"]
            tuplas = filtrar_tuplas(grupo, dominios)

            if not tuplas:
                return False

            permitidos = [set() for _ in variables]
            for tupla in tuplas:
                for posicion, valor in enumerate(tupla):
                    permitidos[posicion].add(valor)

            for variable, valores_permitidos in zip(variables, permitidos):
                nuevo = dominios[variable] & valores_permitidos
                if not nuevo:
                    return False
                if nuevo != dominios[variable]:
                    dominios[variable] = nuevo
                    cambio = True

    return True


def resuelto(dominios):
    return all(len(dominio) == 1 for dominio in dominios.values())


def solucion_valida(grupos, dominios):
    if not resuelto(dominios):
        return False

    for grupo in grupos:
        valores = [next(iter(dominios[var])) for var in grupo["variables"]]
        if len(set(valores)) != len(valores):
            return False
        if sum(valores) != grupo["suma"]:
            return False

    return True


# ============================================
# MRV + DEGREE
# ============================================

def seleccionar_variable(dominios, grupos_por_variable):
    candidatas = [var for var, dominio in dominios.items() if len(dominio) > 1]
    if not candidatas:
        return None

    return min(
        candidatas,
        key=lambda var: (
            len(dominios[var]),
            -len(grupos_por_variable.get(var, [])),
            var,
        ),
    )


def ordenar_valores(variable, dominios, grupos_por_variable):
    valores = []

    for valor in dominios[variable]:
        puntaje = 0
        for grupo in grupos_por_variable.get(variable, []):
            posicion = grupo["variables"].index(variable)
            for tupla in filtrar_tuplas(grupo, dominios):
                if tupla[posicion] == valor:
                    puntaje += 1
        valores.append((puntaje, valor))

    return [valor for _, valor in sorted(valores, reverse=True)]


# ============================================
# BACKTRACKING
# ============================================

def copiar_dominios(dominios):
    return {variable: set(dominio) for variable, dominio in dominios.items()}


def resolver(grupos, dominios, grupos_por_variable, tablero=None, nivel=0):
    global nodos
    global backtracks

    nodos += 1

    if resuelto(dominios):
        return dominios if solucion_valida(grupos, dominios) else None

    variable = seleccionar_variable(dominios, grupos_por_variable)
    if variable is None:
        return None

    for valor in ordenar_valores(variable, dominios, grupos_por_variable):
        copia = copiar_dominios(dominios)
        copia[variable] = {valor}
        tamano_antes = contar_dominios(dominios)

        if propagar(grupos, copia):
            reducciones = tamano_antes - contar_dominios(copia)
            if VERBOSE and tablero is not None:
                mostrar_paso(
                    tablero,
                    copia,
                    variable,
                    valor,
                    nivel,
                    "ok",
                    f"El valor {valor} no rompe ninguna regla. Tambien se eliminaron {reducciones} opciones imposibles.",
                    grupos_por_variable,
                )

            resultado = resolver(grupos, copia, grupos_por_variable, tablero, nivel + 1)
            if resultado is not None:
                return resultado

            if VERBOSE and tablero is not None:
                mostrar_paso(
                    tablero,
                    copia,
                    variable,
                    valor,
                    nivel,
                    "error",
                    "Al principio parecia posible, pero despues obliga al tablero a quedar sin solucion.",
                    grupos_por_variable,
                )
        else:
            if VERBOSE and tablero is not None:
                mostrar_paso(
                    tablero,
                    copia,
                    variable,
                    valor,
                    nivel,
                    "error",
                    "Este valor rompe una regla de inmediato: alguna pista se queda sin opciones validas.",
                    grupos_por_variable,
                )

        backtracks += 1

    return None


# ============================================
# MAIN
# ============================================

def main():
    global VERBOSE
    global nodos
    global backtracks

    nodos = 0
    backtracks = 0
    print_banner()

    respuesta = console.input("\n[bold yellow]Desea ver el proceso paso a paso?[/bold yellow] (s/n): ")
    if respuesta.lower() == "s":
        VERBOSE = True

    archivo = menu_principal()

    console.print()
    console.print(Panel(f"[bold green]Cargando tablero:[/bold green]\n{archivo}", border_style="green"))

    tablero = cargar_tablero(archivo)
    dominios = crear_variables(tablero)
    grupos = crear_grupos(tablero)
    grupos_por_variable = indexar_grupos(grupos)

    console.rule("[bold cyan]GRUPOS GENERADOS[/bold cyan]")
    mostrar_grupos(grupos)

    console.rule("[bold magenta]ESTADO INICIAL[/bold magenta]")
    mostrar(tablero, dominios, "Estado inicial del Kakuro")

    inicio = time.time()

    solucion = None
    if propagar(grupos, dominios):
        solucion = resolver(grupos, dominios, grupos_por_variable, tablero)

    fin = time.time()

    if solucion:
        console.rule("[bold green]KAKURO RESUELTO[/bold green]")
        mostrar(tablero, solucion, "Kakuro resuelto")
    else:
        mostrar_error_rojo(
            "El archivo no se puede solucionar.",
            "Las pistas, dominios o valores fijos generan una contradiccion. "
            "Revise que las sumas sean posibles, que las celdas pertenezcan a sus pistas "
            "y que no existan valores repetidos dentro de un mismo grupo.",
        )

    console.print()
    console.print(
        Panel.fit(
            f"Nodos explorados: [bold cyan]{nodos}[/bold cyan]\n"
            f"Backtracks: [bold red]{backtracks}[/bold red]\n"
            f"Tiempo: [bold green]{fin - inicio:.4f} segundos[/bold green]",
            border_style="bright_blue",
        )
    )


if __name__ == "__main__":
    try:
        main()
    except TableroInvalido as exc:
        mostrar_error_rojo("El archivo plano tiene un error y no se puede solucionar.", str(exc))
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Programa detenido por el usuario.[/bold yellow]")
