# 🚨 Don't change the code below 👇
row1 = ["⬜️","⬜️","⬜️"]
row2 = ["⬜️","⬜️","⬜️"]
row3 = ["⬜️","⬜️","⬜️"]
map = [row1, row2, row3]
print(f"{row1}\n{row2}\n{row3}")
position = input("Where do you want to put the treasure? ")
# 🚨 Don't change the code above 👆

#Write your code below this row 👇

#Save input in Array / List
positionToList= position.split(" ")
horizontal = int(positionToList[0])
vertical = int(positionToList[1])

map[vertical - 1][horizontal - 1] = "X" 

#or 
#First[] selects the Array (row1-3)
#selected_row = map[vertical - 1]
#Second[] selects the Position in the selected Array
#selected_row[horizontal - 1] = "X" 

#Write your code above this row 👆

# 🚨 Don't change the code below 👇
print(f"{row1}\n{row2}\n{row3}")