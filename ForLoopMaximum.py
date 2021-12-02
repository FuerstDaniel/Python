# 🚨 Don't change the code below 👇
student_scores = input("Input a list of student scores ").split()
for n in range(0, len(student_scores)):
  student_scores[n] = int(student_scores[n])
print(student_scores)
# 🚨 Don't change the code above 👆
#Built in functions which you should build with FOR Loops
#print(min(student_scores))
#print(max(student_scores))
#print(len(student_scores))

Student_Counter = 0

highestScore = 0

for score in student_scores:
    if score > highestScore:
        highestScore = score
print(f"The highest Score is {highestScore}")






#Write your code below this row 👇
