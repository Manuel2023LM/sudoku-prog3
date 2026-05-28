# ============================================
# SUDOKU CSP
# Backtracking + Forward Checking + MRV
# ============================================

from copy import deepcopy
import time

from rich import print
from rich.console import Console
from rich.panel import Panel

console = Console()
# Activar o desactivar pasos del backtracking
VERBOSE = False

def print_banner():

    console.clear()

    contenido = (
        "[bold bright_magenta]BIENVENIDO AL JUEGO SUDOKU[/bold bright_magenta]\n\n"
        "[white]Un solucionador compacto con las siguientes técnicas:[/white]\n"
        "[green]• Backtracking[/green]   [yellow]• Forward Checking[/yellow]   [magenta]• Heurística MRV[/magenta]\n"
        "[cyan]• Propagación (AllDifferent)[/cyan]   [bright_blue]• Visualización con rich[/bright_blue]\n\n"
        "[white]Presiona Ctrl+C para salir en cualquier momento.[/white]"
    )

    console.rule("[bold bright_red]— QUE COMIENCE EL JUEGO SUDOKU —", style="bright_red")
    console.print()
    console.print(Panel.fit(contenido, border_style="bright_blue", padding=(1, 6), title="[bold bright_yellow]¡Comencemos![/bold bright_yellow]"), justify="center")
    console.rule("[bold bright_red]— Iniciando Sudoku Solucionador —", style="bright_red")
    console.print()


# ============================================
# VARIABLES DEL SUDOKU
# ============================================

FILAS = "123456789"
COLUMNAS = "ABCDEFGHI"

variables = [c + f for f in FILAS for c in COLUMNAS]

# Contador de nodos
nodos = 0


# ============================================
# LEER ARCHIVO
# ============================================

def cargar_dominios(nombre_archivo):

    dominios = {}

    with open(nombre_archivo, "r") as archivo:

        lineas = [linea.strip() for linea in archivo.readlines()]

    # Verificar que existan exactamente 81 líneas
    if len(lineas) != 81:

        console.print()

        console.print(
            Panel(
                f"[bold red]ERROR EN EL ARCHIVO[/bold red]\n\n"
                f"El archivo Sudoku debe tener exactamente "
                f"[bold yellow]81 líneas[/bold yellow].\n\n"
                f"Líneas encontradas: [bold cyan]{len(lineas)}[/bold cyan]",
                border_style="red"
            )
        )

        raise SystemExit

    for i, variable in enumerate(variables):

        texto = lineas[i]

        # Convierte por ejemplo "3578" -> {3,5,7,8}
        dominios[variable] = set(int(x) for x in texto)

    return dominios


# ============================================
# CREAR RESTRICCIONES
# ============================================

def crear_grupos():

    grupos = []

    # Filas
    for f in FILAS:
        grupos.append([c + f for c in COLUMNAS])

    # Columnas
    for c in COLUMNAS:
        grupos.append([c + f for f in FILAS])

    # Bloques 3x3
    bloques_filas = ["123", "456", "789"]
    bloques_columnas = ["ABC", "DEF", "GHI"]

    for bf in bloques_filas:

        for bc in bloques_columnas:

            bloque = []

            for f in bf:

                for c in bc:

                    bloque.append(c + f)

            grupos.append(bloque)

    return grupos


GRUPOS = crear_grupos()


# ============================================
# MOSTRAR TABLERO
# ============================================

def mostrar(dominios):

    console.print()
    console.print(
        Panel(
            "[bold bright_magenta]Estado actual del Sudoku[/]",
            border_style="bright_magenta",
            style="bold white on black"
        )
    )

    cell_width = 7        # <-- aumentado de 5 a 7
    label_width = 2
    sep = " │ "
    block_sep_w = " ┃ "

    # Encabezado de columnas
    encabezado = " " * (label_width + 4)
    for i, col in enumerate(COLUMNAS):
        encabezado += f"{col:^{cell_width}}"
        if i < 8:
            if i in (2, 5):
                encabezado += "   "   # espacio donde va el ┃
            else:
                encabezado += "   "   # espacio donde va el │
    console.print(f"[bold bright_yellow]{encabezado}[/bold bright_yellow]", no_wrap=True)

    # Bordes horizontales
    block_border = "━" * (cell_width + 3) + "━" + "━" * (cell_width + 3) + "━" + "━" * (cell_width + 1)
    top_border    = "┏" + "━".join([block_border] * 3) + "┓"
    mid_border    = "┣" + "━".join([block_border] * 3) + "┫"
    bottom_border = "┗" + "━".join([block_border] * 3) + "┛"

    console.print(" " * (label_width + 2) + f"[bright_blue]{top_border}[/bright_blue]", no_wrap=True)

    for fila in range(9):
        if fila != 0 and fila % 3 == 0:
            console.print(" " * (label_width + 2) + f"[bright_red]{mid_border}[/bright_red]", no_wrap=True)

        row_cells = []

        for col in range(9):
            variable = variables[fila * 9 + col]
            valor = dominios[variable]

            if len(valor) == 1:
                texto = str(next(iter(valor)))
                formatted = texto.center(cell_width)
                cell = f"[bold bright_white on rgb(20,20,120)]{formatted}[/]"
            else:
                texto = "".join(str(x) for x in sorted(valor))
                if len(texto) > cell_width:
                    texto = texto[: cell_width - 1] + "…"
                formatted = texto.center(cell_width)
                cell = f"[bold red]{formatted}[/]"

            row_cells.append(cell)

        row = (
            f"[bold bright_yellow]{fila + 1:>2}[/bold bright_yellow]  "
            + "[bold bright_red]┃[/bold bright_red] "
            + sep.join(row_cells[0:3])
            + "  [bold bright_red]┃[/bold bright_red] "
            + sep.join(row_cells[3:6])
            + "  [bold bright_red]┃[/bold bright_red] "
            + sep.join(row_cells[6:9])
            + "  [bold bright_red]┃[/bold bright_red]"
        )
        
        console.print(f"[bright_blue]{row}[/bright_blue]", no_wrap=True, style="bold white on black")

    console.print(" " * (label_width + 2) + f"[bright_blue]{bottom_border}[/bright_blue]", no_wrap=True)




# ============================================
# RESTRICCION ALLDIFFERENT
# ============================================

def all_different(dominios, grupo):

    cambio = False

    for var1 in grupo:

        if len(dominios[var1]) == 1:

            valor = next(iter(dominios[var1]))

            for var2 in grupo:

                if var1 != var2 and valor in dominios[var2]:

                    if len(dominios[var2]) > 1:

                        dominios[var2].remove(valor)

                        
                        cambio = True

    return cambio


# ============================================
# VERIFICAR CONFLICTOS
# ============================================

def sin_conflictos(dominios):

    for grupo in GRUPOS:

        vistos = []

        for var in grupo:

            # Solo revisar casillas ya fijas
            if len(dominios[var]) == 1:

                valor = next(iter(dominios[var]))

                # Número repetido
                if valor in vistos:
                    return False

                vistos.append(valor)

    return True



# ============================================
# CONSISTENCIA
# ============================================

def consistente(dominios):

    # Verificar dominios vacíos
    for var in variables:

        if len(dominios[var]) == 0:
            return False

    # Verificar conflictos reales
    if not sin_conflictos(dominios):
        return False

    return True


# ============================================
# PROPAGACION
# ============================================

def propagar(dominios):

    cambio = True

    while cambio:

        cambio = False

        for grupo in GRUPOS:

            if all_different(dominios, grupo):
                cambio = True

        if not consistente(dominios):
            return False

    return True


# ============================================
# VERIFICAR SI ESTA RESUELTO
# ============================================

def resuelto(dominios):

    for var in variables:

        if len(dominios[var]) != 1:
            return False

    return True


# ============================================
# HEURISTICA MRV
# ============================================

def seleccionar_variable(dominios):

    mejor = None
    menor = 10

    for var in variables:

        tamaño = len(dominios[var])

        if 1 < tamaño < menor:

            menor = tamaño
            mejor = var

    return mejor


# ============================================
# BACKTRACKING
# ============================================

def resolver(dominios, nivel=0):

    global nodos
    nodos += 1

    if resuelto(dominios):
        return dominios

    variable = seleccionar_variable(dominios)



    if variable is None:
        return None

    for valor in sorted(dominios[variable]):

        if VERBOSE:

            console.rule(f"[bold yellow]Nivel {nivel}[/bold yellow]")

            console.print(
                f"[bold cyan]Casilla:[/bold cyan] "
                f"{variable}    "
                f"[bold green]Valor:[/bold green] {valor}"
            )


        copia = deepcopy(dominios)

        copia[variable] = {valor}

        if propagar(copia):

            if VERBOSE:

                console.print(
                    f"[bold green]✓ Funciona:[/bold green] "
                    f"{variable} = {valor}"
                )

            resultado = resolver(copia, nivel + 1)

            if resultado is not None:
                return resultado

        

        if VERBOSE:

            console.print(
                f"[bold red]Backtracking:[/bold red] "
                f"{variable} = {valor} no funcionó\n"
            )

    return None


# ============================================
# MAIN
# ============================================

# Mostrar banner primero
# Mostrar banner
print_banner()

# Elegir modo verbose
respuesta = console.input(
    "\n[bold yellow]¿Desea ver el proceso paso a paso?[/bold yellow] "
    "[green](s/n): [/green]"
)

if respuesta.lower() == "s":
    VERBOSE = True

console.print(
    f"[bold green]Modo paso a paso:[/bold green] {VERBOSE}"
    f"[bold blue]\n(si no se muestra nada es porque propagación fue suficiente)[/bold blue]"

)    

dominios = cargar_dominios("sudoku.txt")

console.rule("[bold bright_red]SUDOKU — ESTADO INICIAL[/bold bright_red]", style="bright_red")
mostrar(dominios)

inicio = time.time()

# Propagación inicial
if propagar(dominios):

    if resuelto(dominios):

        console.print()
        console.print(
            Panel(
                "[bold green]Sudoku resuelto únicamente con propagación[/bold green]",
                border_style="green"
            )
        )

        mostrar(dominios)

    else:

        console.print(
            "[yellow]\nLa propagación no fue suficiente. "
            "Iniciando búsqueda...\n[/yellow]"
        )

        console.rule("[bold yellow]INICIANDO BACKTRACKING[/bold yellow]")



        if VERBOSE:
            console.print(
                "[bold cyan]Mostrando decisiones del backtracking...[/bold cyan]"
            )

        solucion = resolver(dominios)

        if solucion:
            console.print(Panel("[bold green]SUDOKU RESUELTO[/bold green]", border_style="green", style="bold green on black"))
            mostrar(solucion)

        else:
            console.print(Panel("[bold red]No se encontró solución[/bold red]", border_style="red"))

else:
    console.print(Panel("[bold red]Sudoku inconsistente[/bold red]", border_style="red"))

fin = time.time()

console.print()
console.print(Panel.fit(f"Nodos explorados: [bold cyan]{nodos}[/bold cyan]\nTiempo de ejecución: [bold cyan]{fin - inicio:.4f} s[/bold cyan]", border_style="bright_cyan"))