################################################################################
#
# Sends email for each employee that didn't start their timesheet.
#
################################################################################

def pending_list():
    import pandas as pd
    import os
    from pathlib import Path

    # Path to df data.
    os.chdir(Path.home() / "Downloads")
    Downloads_list = os.listdir()

    for item in Downloads_list:
        if "&_Comments Report" in item:
            pendingList = item
            break

    # Create Data Frame.
    # NOTE: should be try except statement.
    if os.path.isfile(pendingList):
        df = pd.read_csv(pendingList)
    else:
        print(f"Failed to import {pendingList}")

    # List of headers to make it easy.
    headers = df.columns.to_list()
    # These are the only ones that matter.
    # NOTE: make an alternative to send managers list of all.
    df = df[(df[headers[14]] == "Pending")]
    return df[headers[21]].unique().tolist()


if __name__ == "__main__":
    mylist = "; ".join(pending_list()) # Outlook can only take a ; seperated list.

    try:
        import win32com.client

        # Create Outlook object
        outlook = win32com.client.Dispatch("Outlook.Application")

        # Create Email object
        message = outlook.CreateItem(0)

        # This is CC.
        #message.CC = 

        # This is BCC.
        message.BCC = mylist

        # Subject Line.
        message.Subject = "Timesheets Ready for Approval"

        # Attachements.
        #message.Attachments.Add(full_path)

        # Body of message / HTML Body.
        message.Body = \
"""\
Hi,
        
There are Timesheets ready for your approval. If you need anything, please let me know.
        
Wesley Blake
Human Resources Analyst II\
"""

        message.Display()
    except:
        print("Failed to send: Pending List")