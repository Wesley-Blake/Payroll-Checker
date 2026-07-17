# Guidelines For Refactor.
1. There are 4 reports the will display information.
    1. status of the timesheet
    2. overlapping hours
    3. not started
    4. breakdown of hours
2. There should be a parrent class.
    1. method to find the csv report in downloads
    2. method to make the dataframe
        1. input should be a list of headers to keep, drop the rest
3. There should be 1 object for each report.
    * input is csv
    * attribute is a dataframe of that csv
    * Each method should check for 1 specific type of error and return a list of emails (unique)
4. Function to determine current pay period.

# Pay Schedule
1. Payroll reports every 2 weeks.
2. All reports are limited to those two weeks.

# Earn Code Rules BY Employee Type (ECLS)
1. REG or Regular Hours.
    1. OO, PP, WW
        1. should be 40 hours in a week or 80 in a pay period.
        2. shouldn't be more than 8 hours in a day.
    2. UU, VV:
        1. should be 37.5 hours in a week or 75 in a pay period.
        2. shouldn't be more than 7.5 hours in a day.
2. VAC or Vacation.
    1. only the following get Vacation time
        1. OO,PP = 8 hours in a day 40 in a week
        2. UU,VV = 7.5 hours in a day 37.5 in a week
3. SICK or Sick hours.
    * Everyone gets SICK
    1. OO, PP, WW
        1. should be 40 hours in a week or 80 in a pay period.
        2. shouldn't be more than 8 hours in a day.
    2. UU, VV:
        1. should be 37.5 hours in a week or 75 in a pay period.
        2. shouldn't be more than 7.5 hours in a day.
4. HOL or Holiday Pay.
    * This will only happen on special days of the year. List of dates should be provided.
    1. only the following get Holiday Pay
        1. OO,PP = 8 hours in a day 40 in a week
        2. UU,VV = 7.5 hours in a day 37.5 in a week
5. HLW or Holiday Worked.
    * This will only happen and overlap with HOL.
    * Same rules as HOL.
6. OT or Overtime.
    * Only occures after the dailey limit or weekly limit of REG.
7. OT2 or Overtime 2x.
    * Only occures after the sum of REG, HLW, and OT hit 12 hours in a single day.
8. SHF or Shift Differential.
    * Only UU and VV get this code.
    * Can only happen after 1800 or 6pm.
    * Does not overlap with OT or OT2.
    * Can only Overlap with REG.
9. PER or Personal Holiday.
    * Only UU and VV get this code.
    * limit to 7.5 hours in a day.
10. MD or Medical Dental.
    * Only UU and VV get this code.
    * Shouldn't be more than 7.5 hours in a day.
11. BRV or Bereavement.
    * Not more than 5 days of this code.
    1. only the following get Bereavement
        1. OO,PP = 8 hours in a day 40 in a week
        2. UU,VV = 7.5 hours in a day 37.5 in a week
12. VLT or Volunteer Time and JRY or Jury Duty Time.
    1. only the following get Volunteer Time or Jury Duty Time
        1. OO,PP = 8 hours in a day 40 in a week
        2. UU,VV = 7.5 hours in a day 37.5 in a week