# Split string method
names_string = input("Give me everybody's names, separated by a comma. ")
names = names_string.split(", ")
# 🚨 Don't change the code above 👆

#Write 
import random

listlenght = len(names)

randInt = random.randint(0, listlenght - 1)

print(f"{names[randInt]} is going to pay the Bill")


