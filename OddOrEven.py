#Write your code below this line 👇
check = 0

while check == 0 :
    number = int(input("Which number do you want to check? "))
    if number % 2 == 0:
        print("Number is Even")
    else:
        print("Number is odd")

    print("Do you want to check another Number? Y/N")
    if input() == "Y":
        Check=0
    else:
        input() == "N"
        Check=1
        break


