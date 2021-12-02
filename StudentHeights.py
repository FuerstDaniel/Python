# 🚨 Don't change the code below 👇
student_heights = input("Input a list of student heights ").split()
for n in range(0, len(student_heights)):
  student_heights[n] = int(student_heights[n])
# 🚨 Don't change the code above 👆
Student_Counter =  0
total_height = 0 

for height in student_heights:
    Student_Counter += 1
    total_height += height
Calc = float(total_height // Student_Counter)

print(f"Der Durchschnitt ist {Calc}")
print(f"Es sind {Student_Counter} Studenten")
#Write your code below this row 👇



