rock = '''
    _______
---'   ____)
      (_____)
      (_____)
      (____)
---.__(___)
'''

paper = '''
    _______
---'   ____)____
          ______)
          _______)
         _______)
---.__________)
'''

scissors = '''
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)
'''

#Write your code below this line 👇

import random

#Runde
roundcounter=0
WinHum = 0
WinComp = 0

#gameImages = [rock, paper, scissors]

# Es wird 3 Runden gespielt
while roundcounter < 3:

    human = int(input("Was wählst du? 0 Für Stein, 1 für Papier, 2 für Schere \n"))
   # print(gameImages[human])
    computer = random.randint(0, 2)
    #print(gameImages[human])
    roundcounter += 1

    if human == 0:
        print(f"Du hast den Stein gewählt {rock} ")
    elif human == 1:
        print(f"Du hast das Papier gewählt {paper} ")
    elif human == 2:
        print(f"Du hast die Schere gewählt {scissors} ")
    else:
        print("Invalid Number")

    if computer == 0:
        print(f"Computer hat den Stein gewählt {rock} ")
    elif computer == 1:
        print(f"Computer hat das Papier gewählt {paper} ")
    elif computer == 2:
        print(f"Computer hat die Schere gewählt {scissors} ")

    if human == 0 and computer == 2:
        print("Du hast gewonnen")
        WinHum += 1
    elif human == computer:
        print("Unentschieden")    
    elif human == 2 and computer == 1:
        print("Du hast gewonnen")
        WinHum += 1
    elif human == 1 and computer == 0:
        print    
        WinHum += 1
    else:
        print("Computer hat gewonnen")
        WinComp += 1
    
    if roundcounter == 3 and WinHum == WinComp:
        print(f"Aktuell herrscht gleichstand es wird noch eine Runde gespielt {WinHum} : {WinComp} ")
        roundcounter -=1
        
if WinHum > WinComp:
    print(f"Du hast {WinHum} : {WinComp} gewonnen ")
elif WinHum == WinComp:
    print(f"Unentschieden {WinHum} : {WinComp} ")
else:
    print(f"Der Computer hat {WinComp} : {WinHum} gewonnen")



