#If the bill was $150.00, split between 5 people, with 12% tip. 

#Each person should pay (150.00 / 5) * 1.12 = 33.6
#Format the result to 2 decimal places = 33.60

#Tip: There are 2 ways to round a number. You might have to do some Googling to solve this.💪

#Write your code below this line 👇

Bill = float(input("Welcome to the tip calculator.\n What was the total bill? "))

Tip = int(input("How much Percent of Tip?"))

people = int(input("How many people should split?"))

amount_per_User = "{:.2f}".format((((Tip/100*Bill)+100)/people)) 
print(f"Each person should pay: {amount_per_User}" )

#test