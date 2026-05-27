# =========================================
# CLASS MARK CALCULATOR SYSTEM
# =========================================

students = []

# Number of students
num_students = int(input("Enter number of students: "))

# Input student names and marks
for i in range(num_students):
    print(f"\nStudent {i + 1}")
    
    name = input("Enter student name: ")
    mark = float(input("Enter student mark: "))

    students.append((name, mark))

# =========================================
# CALCULATIONS
# =========================================

# Extract marks only
marks = [mark for name, mark in students]

# Average
average = sum(marks) / len(marks)


# Integer division
groups = num_students // 5
print("Groups of 5 students:", groups)

# Modulus and ==
if mark % 2 == 0:
    print("Even mark")
else:
    print("Odd mark"

# Minimum and Maximum
minimum = min(marks)
maximum = max(marks)

# Distinctions (75% and above)
distinctions = [(name, mark) for name, mark in students if mark >= 75]

# Sort students from highest to lowest
sorted_students = sorted(students, key=lambda x: x[1], reverse=True)

# Top 10 performers
top_10 = sorted_students[:10]

# =========================================
# OUTPUT SECTION
# =========================================

print("\n=================================")
print("     CLASS PERFORMANCE REPORT")
print("=================================")

print(f"\nClass Average: {average:.2f}%")
print(f"Highest Mark: {maximum}%")
print(f"Lowest Mark: {minimum}%")

# Distinction Students
print("\n--- DISTINCTIONS ---")

if distinctions:
    for name, mark in distinctions:
        print(f"{name}: {mark}%")
else:
    print("No distinctions found.")

# Top 10 Students
print("\n--- TOP 10 BEST PERFORMERS ---")

for position, (name, mark) in enumerate(top_10, start=1):
    print(f"{position}. {name} - {mark}%")

print("\n=================================")
print("      END OF REPORT")
print("=================================")
