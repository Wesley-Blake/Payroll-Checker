################################################################################
#
# Sends email for each employee that have overlapping hours, that shouldn't.
#
################################################################################
import pandas as pd
import os
from pathlib import Path

def wrong_overlapping_hours() -> list:
    # Read most recent overlapping hours file
    os.chdir(Path.home() / "Downloads")
    downloads_list = os.listdir()

    # NOTE: update to find to find most receint then run "downloads-cleaning.py".
    for item in downloads_list:
        if "Empls_with_Overlapping_Hours" in item:
            overlap_hours = item
            break
    
    # NOTE: should be try except statement.
    if os.path.isfile(overlap_hours):
        df = pd.read_csv(overlap_hours)
    else:
        print(f"Failed to import {overlap_hours}")

    # Check for codes that aren't REG && SHF
    headers = df.columns.to_list()
    wrong_overlap = df[(df[headers[11]] != "REG") & \
            (df[headers[11]] != "SHF")]

    if wrong_overlap.empty:
        input("wrong overlap empty")
        return None
    else:
        return wrong_overlap[headers[16]].unique().tolist()

def wrong_shf_hours() -> list:
     # Read most recent overlapping hours file
    os.chdir(Path.home() / "Downloads")
    downloads_list = os.listdir()

    # NOTE: This should be its own function.
    # NOTE: update to find to find most receint then run "downloads-cleaning.py".
    for item in downloads_list:
        if "Empls_with_Overlapping_Hours" in item:
            overlap_hours = item
            break
    
    # NOTE: should be try except statement.
    if os.path.isfile(overlap_hours):
        df = pd.read_csv(overlap_hours)
    else:
        print(f"Fail to import {overlap_hours}")
    # NOTE: End of own function

    # Check for codes that aren't REG && SHF
    headers = df.columns.to_list()
    # SHF != 1800 in time
    wrong_shf = df[(df[headers[11]] == "SHF") & \
                   (df[headers[14]] != 1800)]
    if wrong_shf.empty:
        input("wrong shf empty")
        exit() # This runs last, so it is fine to cut it here.
    else:
        return wrong_shf[headers[16]].unique().tolist()
        


if __name__ == "__main__":
    # Email for wrong overlap
    temp = wrong_overlapping_hours()
    if temp is not None:
        email_list = "; ".join(temp) # Outlook can only take a ; seperated list.

        try:
            import win32com.client

            # Create Outlook object
            outlook = win32com.client.Dispatch("Outlook.Application")

            # Create Email object
            message = outlook.CreateItem(0)

            # This is BCC.
            message.BCC = email_list

            # Subject Line.
            message.Subject = "Overlapping Hours Error"

            # Body of message / HTML Body.
            message.Body = \
"""\
Hi,
            
If you are recieving this message, you have overlapping hours on your Timesheet. If you have any questions, let me know :)
        
Wesley Blake
Human Resources Analyst II\
"""

            message.Display()
        except:
            print("Failed to send: overlapping hours email")

    # Email about wrong SHF
    email_list = "; ".join(wrong_shf_hours()) # Outlook can only take a ; seperated list.

    try:
        import win32com.client

        # Create Outlook object
        outlook = win32com.client.Dispatch("Outlook.Application")

        # Create Email object
        message = outlook.CreateItem(0)

        # This is BCC.
        message.BCC = email_list

        # Subject Line.
        message.Subject = "Overlapping Hours Error"

        # Body of message / HTML Body.
        message.Body = \
"""\
Hi,
        
If you are recieving this message, you may have incorrect Shift differential hours. If you have any questions, let me know :)
        
Wesley Blake
Human Resources Analyst II\
"""

        message.Display()
    except:
        print("Failed to send: SHF email")