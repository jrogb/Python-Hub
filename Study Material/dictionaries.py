#Creating a dictionary

#Dictionaries are key, value stores in python.  Keys are unmutable while values can be modified and of any type.

student = {
    "name": "Johan",
    "id": 12,
    "courses": ["NET512","MAT511","FIN123","PROG511"]
}

#Displaying the dictionary
print(f'Student Dictionary: {student}')
#Accessing values in a dictionary
print(f'Student Name: {student["name"]}\nStudent ID: {student["id"]}\nStudent Courses: {student["courses"]}')

#Adding information to a dictionary
student["surname"] = "Grobbelaar"
print(student)