"""
a= 3 
b= 2

c = a+b

print(c)

"""

numero1= int (input("ingrese un numero "))

numero2= int (input("ingrese otro numero "))





op = 0

while op != 5: 

    print("======== *MENU DE OPCIONES* ========")



    print("1 Suma")

    print("2 Resta")

    print("3 Multiplicacion")

    print("4 Division")


    print("5 SALIR DE MENU")
    

    op = int(input("ingrese una opcion "))

    suma = numero1 + numero2


    resta = numero1 - numero2


    multiplicacion = numero1 * numero2


    division = numero1 / numero2




    if op == 1:
    
        print("la suma es :",suma)



    if op == 2:
    
     print("la resta es :",resta)


    if op == 3:
    
        print("la multiplicacion es :",multiplicacion)


    if op == 4:
    
        print("la division es :",division)


    if op == 5:
        print("saliendo")



print ("hola mundo")