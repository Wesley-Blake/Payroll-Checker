"""Email body templates for each payroll check, rendered via `render()`.

Every template is a `string.Template` ending in `${timesheet_link}`, so a
single call shape (`render(TEMPLATE, timesheet_link=..., **extra)`) works
for all of them regardless of whether they also need other placeholders
(e.g. the holiday templates' `${list_o_holidays}`).
"""

from string import Template


def render(template: Template, **kwargs: str) -> str:
    """Render an email body template, substituting all placeholders."""
    return template.substitute(**kwargs)


HOLIDAY_DATE_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Holiday / Holiday Worked was detected.
Holiday and or Holiday Worked was reported on the incorrect day.
${list_o_holidays}
${timesheet_link}""")

HOLIDAY_TYPE_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Holiday / Holiday Worked was detected.
Holiday Pay doesn't reflect on the holiday.
${list_o_holidays}
${timesheet_link}""")

NOT_STARTED_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Timesheet Not Started
If you haven't worked, then you wouldn't need to do anyhting, but if you have worked, please start your timesheet and fill in your hours for the pay period.

${timesheet_link}""")

INCORRECT_EARN_CODE_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Incorrect Earn Code Detected see below list.
[ SHD ]

${timesheet_link}""")

OVERTIME_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Overtime Not Allocated

We wanted to let you know that you recorded more than 8 hours of regular (7.5 for union) time in a single day, and overtime has not yet been allocated.

For helpful guidance, you can review the overtime rules here: https://www.dir.ca.gov/dlse/FAQ_Overtime.htm
Essentially, you should put 8 (7.5 union) in Regular Earnings, the rest goes in Overtime.
${timesheet_link}""")

OVER_TWELVE_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Overtime for Hours Over 12 Not Allocated

We wanted to share a quick reminder that any hours worked over 12 in a single day (regular + overtime) are automatically considered OT2 and may need to be allocated accordingly.
For more information, you can review the guidelines here: https://www.dir.ca.gov/dlse/FAQ_Overtime.htm
Example:
8 REG (7.5 union) + 4 OT (4.5 union) = 12 hours and everything else is in OT2.
${timesheet_link}""")

WEEKEND_OT_TEMPLATE = Template("""\
Hi,
Friendly Reminder: Weekend Overtime Detected
We noticed that you recorded more than 40 hours of regular time in a week.
Overtime for hours over 40 in a week hasn't been allocated yet.
For helpful guidance, you can review the overtime rules here: https://www.dir.ca.gov/dlse/FAQ_Overtime.htm
${timesheet_link}""")

UNION_WEEKEND_OT_TEMPLATE = Template("""\
Hi,
Friendly Reminder: Union Weekend Overtime Detected
We noticed that your timesheet includes more than 5 unique days of regular hours in a Monday-Sunday week.
Please review your timesheet and allocate overtime if appropriate.
For guidance, you can review the overtime rules in the union contract.
${timesheet_link}""")

UNION_WEEKEND_OT2_TEMPLATE = Template("""\
Hi,
Friendly Reminder: Union Weekend OT2 Detected
We noticed that on your 6th or 7th consecutive day of regular hours in a Monday-Sunday week, you recorded more than 7.5 hours.
Hours over 7.5 on that day need to be allocated as OT2, not regular overtime.
For guidance, you can review the overtime rules in the union contract.
${timesheet_link}""")

SHF_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Shift Differential Issue Detected

We noticed a problem with Shift Differential (SHF) on your timesheet. A quick review of the rules:
Shift Differential is for union employees only, starts at or after 6:00pm, and should end when the matching Regular Earnings entry ends.
If you worked Regular hours past 6:00pm, please add a matching SHF entry; if SHF was entered outside these rules, please correct it.
${timesheet_link}""")

OVERLAPPING_TEMPLATE = Template("""\
Hi,

Friendly Reminder: Overlapping Hours

We noticed that there are some hours on your timesheet that overlap. This happens from time to time and can usually be resolved with a quick review.
Additionally, if you are using the Employee Services (new), the yellow (!) will tell you specifics.
${timesheet_link}""")

PENDING_TEMPLATE = Template("""\
Hi,

Manager Reminder: Pending Approvals

Just a quick heads-up that you have employees whose timesheets are currently in a pending status and ready for your approval when you have a moment.

Thanks so much for your time and support!
${timesheet_link}""")
