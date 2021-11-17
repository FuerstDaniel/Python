# 🚨 Don't change the code below 👇
height = float(input("enter your height in m: "))
weight = float(input("enter your weight in kg: "))
# 🚨 Don't change the code above 👆

#Write your code below this line 👇

BMI=round(((weight / height ** 2 )))

if BMI < 18.5:
    print("you are underweight")
    print(f"Your BMI is {BMI}")
elif BMI <= 25:
    print("you are normal weight")
    print(f"Your BMI is {BMI}")
elif BMI <= 28:
    print("you are slightly overweight or well trained :)")
    print(f"Your BMI is {BMI}")
elif BMI <= 33:
    print("you are overweight or an ox") 
    print(f"Your BMI is {BMI}")
elif BMI <= 40:
    print("well maybe your an fat ass dude or you're a beast. Congrats")   
    print(f"Your BMI is {BMI}")    

