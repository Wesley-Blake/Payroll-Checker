################################################################################
#
# Sends email for each employee that didn't start their timesheet.
#
################################################################################

def not_started_appEmail() -> list:
    import pandas as pd
    import os
    from pathlib import Path

    # Path to df data.
    os.chdir(Path.home() / "Downloads")
    downloads_list = os.listdir()

    # NOTE: update to find to find most receint then run "downloads-cleaning.py".
    for item in downloads_list:
        if "not_yet_started_WTE" in item:
            not_started = item
            break

    # Create Data Frame.
    # NOTE: should be try except statement.
    if os.path.isfile(not_started):
        df = pd.read_csv(not_started)
    else:
        print(f"Failed to import {not_started}")
            
    # List of headers to make it easy.
    headers = df.columns.to_list()
    # We only care about these jobes.
    df = df[(df[headers[16]] == "OO") | \
        #(df[headers[16]] == "PP") | \ # I might need this later.
        (df[headers[16]] == "UU") | \
        (df[headers[16]] == "VV")]

    return df[headers[20]].unique().tolist()


if __name__ == "__main__":
    mylist = "; ".join(not_started_appEmail()) # Outlook can only take a ; seperated list.

    try:
        import win32com.client

        # Create Outlook object
        outlook = win32com.client.Dispatch("Outlook.Application")

        # Create Email object
        message = outlook.CreateItem(0)

        # This is CC, This might be used.
        #message.CC = 

        # This is BCC.
        message.BCC = mylist

        # Subject Line.
        message.Subject = "Timesheet Not Started"

        # Attachements. This might be used.
        #message.Attachments.Add(full_path)

        # Body of message / HTML Body.
        message.Body = \
"""\
Hi,
        
If you are recieving this message, you haven't started your Timesheet, please do so now. If you have any questions, let me know :)
        
Wesley Blake
Human Resources Analyst II\
"""

        message.Display() # Displays message so I can see it before it is sent.
    except:
        print("Failed to send: Not Started WTE")