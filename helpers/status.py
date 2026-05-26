import pandas
from pandas import DataFrame
from helpers.support import *


def not_started_list(file: DataFrame) -> list[str]:
    logger = setup_logger("PayRollChecker.log")
    white_list = ["EmplID", "job_ecls", "EmplEmail", "ApprEmail"]
    #file = file[white_list]
    final_df = file[white_list]
    #final_df = file[
    #    (file["job_ecls"] != "SS") &
    #    (file["job_ecls"] != "SN") &
    #    (file["job_ecls"] != "WW")
    #]
    if final_df.empty:
        logger.info("All employees started.")
        return []

    logger.info("Finished Successfully.")
    return make_list(final_df["EmplEmail"].unique().tolist())

def pending(file: DataFrame) -> list[str]:
    # NOTE: implement return_dict
    import validators
    logger = setup_logger("PayRollChecker.log")
    final_df = file[file["ts_Status"] == "Pending"]
    if final_df.empty:
        logger.info("No employees in pending.")
        return []

    manager_emails = final_df["ApprEmail"].unique().tolist()
    for email in manager_emails:
        if not validators.email(email):
            logger.debug("Manager emails not emails.")
            return []
    logger.info("Finished Successfully.")
    return make_list(manager_emails)
