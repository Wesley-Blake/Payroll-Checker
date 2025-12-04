# Payroll-Checker
I use this to check paryoll for basic things.

# My idea
I had two options, 
1. Scan for errors them selves.
    1. This would be a funciton for each error to generate a list of emails to send.
    2. function() -> dictonary[key: manager email, value: list(employee email)]
    3. Issue: a manager and employee could potentially get multiple emails.
2. Employee email with list of errors.
    1. Start with the dictonary of employee emails and append a error message to the list for each employee.
    2. dictonary[key: employee email, values: function()-> list.append(erros)]
    3. Issue: manager woudn't be in email becuase an employee could have multiple jobs with different managers.