#Password Generator Project
import random
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

print("Welcome to the PyPassword Generator!")
nr_letters= int(input("How many letters would you like in your password?\n")) 
nr_symbols = int(input(f"How many symbols would you like?\n"))
nr_numbers = int(input(f"How many numbers would you like?\n"))

#Eazy Level - Order not randomised:
#e.g. 4 letter, 2 symbol, 2 number = JduE&!91

GenerateLetters = []
GenerateSymbols = []
GenerateNumbers = []
Password_List = [GenerateLetters, GenerateSymbols, GenerateNumbers]
Enhancend_List = []
Hardened_Password = []


random_integer_for_Letter =0 

for letter in range(0, (nr_letters) ):
    random_integer_for_Letter = random.randint(0, int(len(letters)))
    GenerateLetters += letters[random_integer_for_Letter - 1]
    


random_integer_for_symbol = 0

for symbol in range(0, nr_symbols):
    random_integer_for_symbol = random.randint(0, int(len(symbols)))
    GenerateSymbols += symbols[random_integer_for_symbol - 1] 


random_integer_for_numbers = 0

for number in range(0, nr_numbers):
    random_integer_for_numbers = random.randint(0, int(len(numbers)))
    GenerateNumbers += numbers[random_integer_for_numbers - 1]


password = ""
for item in Password_List:
    ConvToStr = "".join(item)
    password += ConvToStr

print(password)







#Hard Level - Order of characters randomised:
#e.g. 4 letter, 2 symbol, 2 number = g^2jk8&P

for item in Password_List:
        
    randomChar = random.randint(0, len(Password_List-1))

    Hardened_Password[randomChar] += item

