
#Write your code below this line 👇
a = 0

while a == 0 :
    year = int(input("Which year do you want to check? "))

    if year % 4 == 0:
    
        if year % 100 == 0:
            if year % 400 == 0:
                print("Leap Year - Do you want to check another Year? y/n")
                if input() == "y":
                    a=0
                else:
                    input() == "n"
                    a=1
                    break
            else:
                print("No Leap Year - Do you want to check another Year? y/n")
                if input() == "y":
                    a=0
                else :
                    input() == "n"
                    a=1
                    break    
        else:
            print("Leap Year - Do you want to check another Year? y/n")
            if input() == "y":
                a=0
            else :
                input() == "n"
                a=1
                break
    else:
        print("No Leap Year - Do you want to check another Year? y/n")
        if input() == "y":
                a=0
        else :
            input() == "n"
            a=1
            break
