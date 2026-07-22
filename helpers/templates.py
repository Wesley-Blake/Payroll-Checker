from string import Template

# NO_HOLIDAY_TEMPLATE = """\
# Hi,
#
# Friendly Reminder: Holiday / Holiday Worked was detected.
# There wasn't a holiday this pay period.
# """

HOLIDAY_DATE_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Holiday / Holiday Worked was detected.
Holiday and or Holiday Worked was reported on the incorrect day.
${list_o_holidays}
""")

HOLIDAY_TYPE_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Holiday / Holiday Worked was detected.
Holiday Pay doesn't reflect on the holiday.
${list_o_holidays}
""")

NOT_STARTED_TEMPLATE = """\
Hi,

Friendly Reminder: Timesheet Not Started
If you haven't worked, then you wouldn't need to do anyhting, but if you have worked, please start your timesheet and fill in your hours for the pay period.

"""

INCORRECT_EARN_CODE_TEMPLATE = """\
Hi,

Friendly Reminder: Incorrect Earn Code Detected see below list.
[ SHD ]

"""

OVERTIME_TEMPLATE = """\
Hi,

Friendly Reminder: Overtime Not Allocated

We wanted to let you know that you recorded more than 8 hours of regular (7.5 for union) time in a single day, and overtime has not yet been allocated.

For helpful guidance, you can review the overtime rules here: https://www.dir.ca.gov/dlse/FAQ_Overtime.htm
Essentially, you should put 8 (7.5 union) in Regular Earnings, the rest goes in Overtime.
"""

OVER_TWELVE_TEMPLATE = """\
Hi,

Friendly Reminder: Overtime for Hours Over 12 Not Allocated

We wanted to share a quick reminder that any hours worked over 12 in a single day (regular + overtime) are automatically considered OT2 and may need to be allocated accordingly.
For more information, you can review the guidelines here: https://www.dir.ca.gov/dlse/FAQ_Overtime.htm
Example:
8 REG (7.5 union) + 4 OT (4.5 union) = 12 hours and everything else is in OT2.
"""

WEEKEND_OT_TEMPLATE = """\
Hi,
Friendly Reminder: Weekend Overtime Detected
We noticed that you recorded more than 40 hours of regular time in a week.
Overtime for hours over 40 in a week hasn't been allocated yet.
For helpful guidance, you can review the overtime rules here: https://www.dir.ca.gov/dlse/FAQ_Overtime.htm
"""

UNION_WEEKEND_OT_TEMPLATE = """\
Hi,
Friendly Reminder: Union Weekend Overtime Detected
We noticed that your timesheet includes more than 5 unique days of regular hours in a Monday-Sunday week.
Please review your timesheet and allocate overtime if appropriate.
For guidance, you can review the overtime rules in the union contract.
"""

OVERLAPPING_TEMPLATE = """\
Hi,

Friendly Reminder: Overlapping Hours

We noticed that there are some hours on your timesheet that overlap. This happens from time to time and can usually be resolved with a quick review.
Additionally, if you are using the Employee Services (new), the yellow (!) will tell you specifics.
"""

PENDING_TEMPLATE = """\
Hi,

Manager Reminder: Pending Approvals

Just a quick heads-up that you have employees whose timesheets are currently in a pending status and ready for your approval when you have a moment.

Thanks so much for your time and support!
"""

# MANAGER_TEMPLATE = Template("""\n
# Manager Notification:
# You're receiving this email because ${length} of your employees have a timesheet item to review for the pay period ${PAY_PERIOD}.
# They've been BCC'd on this message as a helpful reminder, so no action is needed from you at this time.
#
# Thanks so much, and have a great day!
# """
# )
