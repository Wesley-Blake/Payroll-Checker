###############################
#
# Clean up downloads folder
#
###############################

import os, shutil
from pathlib import Path

# Home navigation
try:
    os.chdir(Path.home() / "Documents")
except Exception as e:
    print(e)
    input("Initial os.chdir failed.")
    exit()

# Get directory locations
try:
    with open("myPaths.txt","r") as file:
        docs = file.readline().replace("\n","").rstrip() # remove /n & white space (right)
        downloads = file.readline().replace("\n","").rstrip()
        payroll = file.readline().replace("\n","").rstrip()
except Exception as e:
    print(e)
    input("Directory variables failed.")
    exit()

# Get current pay period directory
# NOTE: update this to find most recent payroll #
try:
    os.chdir(payroll)
    for item in os.listdir():
        if "_onbased" not in item and "#" in item:
            os.chdir(item)
            if "Argos" in os.listdir():
                payroll = Path.cwd() / "Argos"
                break
            else:
                os.mkdir("Argos")
                payroll = Path.cwd() / "Argos"
                break

except Exception as e:
    print(e)
    input("Failed to change Dir in Payroll folder (argos).")
    exit()

# Find files to move
os.chdir(downloads)
list = os.listdir()
counter = 0 # Count of files not moved.
 
# Move my files payroll directory
for item in list:
    match item[:-27]: # Removes part of file name I don't want.
        case "Empls_who_not_yet_started_WTE_Timesheets":
            try:
                shutil.move(item ,payroll)
            except Exception as e:
                print(f"{item}: {e}")
                counter += 1
        case "Time_Sheet_Status_&_Comments":
            try:
                shutil.move(item ,payroll)
            except Exception as e:
                print(f"{item}: {e}")
                counter += 1
        case "Empls_with_Overlapping_Hours":
            try:
                shutil.move(item ,payroll)
            except Exception as e:
                print(f"{item}: {e}")
                counter += 1
        case "6_Consecutive_Work_Days_from_specified_date":
            try:
                shutil.move(item ,payroll)
            except Exception as e:
                print(f"{item}: {e}")
                counter += 1
        case "7_Consecutive_Work_Days":
            try:
                shutil.move(item ,payroll)
            except Exception as e:
                print(f"{item}: {e}")
                counter += 1
        case "ts_break_down_in_out_hours_by_earn_code CSV":
            try:
                shutil.move(item ,payroll)
            except Exception as e:
                print(f"{item}: {e}")
                counter += 1
        case _:
            continue

input(f"{counter}, files not moved.") # Keeps the shell open so I can read it.