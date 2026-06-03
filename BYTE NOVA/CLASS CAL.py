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

    while True:
        mark = float(input("Enter student mark: "))
        if 0 <= mark <= 100:
            break
        print("Please enter a mark between 0 and 100.")

    students.append((name, mark))

# =========================================
# CALCULATIONS
# =========================================

# Extract marks
marks = [mark for name, mark in students]

# Average mark
average = sum(marks) / len(marks)

# Number of groups of 5 students
groups = num_students // 5

# Minimum and maximum marks
minimum = min(marks)
maximum = max(marks)

# Performance prediction
if average >= 75:
    prediction = "Excellent performance expected."
elif average >= 50:
    prediction = "Likely to pass with consistent effort."
else:
    prediction = "Additional support may be required."

# Students with distinctions (75% and above)
distinctions = [
    (name, mark) for name, mark in students
    if mark >= 75
]

# Sort students from highest to lowest
sorted_students = sorted(
    students,
    key=lambda student: student[1],
    reverse=True
)

# Top 10 performers
top_10 = sorted_students[:10]

# =========================================
# OUTPUT SECTION
# =========================================

print("\n=================================")
print("      CLASS PERFORMANCE REPORT")
print("=================================")

print(f"\nClass Average: {average:.2f}%")
print(f"Highest Mark: {maximum}%")
print(f"Lowest Mark: {minimum}%")
print(f"Groups of 5 Students: {groups}")
print(f"Prediction: {prediction}")

# Even/Odd mark check for each student
print("\n--- EVEN / ODD MARKS ---")
for name, mark in students:
    if mark % 2 == 0:
        print(f"{name}: {mark}% (Even)")
    else:
        print(f"{name}: {mark}% (Odd)")

# Distinction students
print("\n--- DISTINCTIONS ---")
if distinctions:
    for name, mark in distinctions:
        print(f"{name}: {mark}%")
else:
    print("No distinctions found.")

# Top 10 students
print("\n--- TOP 10 BEST PERFORMERS ---")
for position, (name, mark) in enumerate(top_10, start=1):
    print(f"{position}. {name} - {mark}%")

print("\n=================================")
print("        END OF REPORT")
print("=================================")
