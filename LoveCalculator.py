# 🚨 Don't change the code below 👇
print("Welcome to the Love Calculator!")
name1 = input("What is your name? \n")
name2 = input("What is their name? \n")
# 🚨 Don't change the code above 👆

#Write your code below this line 👇

#T#L
#R#o
#U#v
#E#e


Counter = 0
combined_string = name1 + name2
lower_case_string = combined_string.lower()


for char in lower_case_string:
    if char == "t" or char == "r" or char == "u" or char == "e":
        Counter +=1

counterFirstWord = int(Counter)
Counter=0

for char in lower_case_string:
    if char == "l" or char == "o" or char == "v" or char == "e":
        Counter +=1

counterSecondWord = int(Counter)

FirstNumber =  str(counterFirstWord)
SecondNumber = str(counterSecondWord)

percent = int(FirstNumber + SecondNumber)

if percent <= 10 and percent >= 90:
    print(f"Your Score is {percent} you go together like coke and Mentos")

if percent >= 40 and percent <=50:
    print(f"Your Score is {percent} you are alright together")

else:
    print(f"Your Score is {percent}")

