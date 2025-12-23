# Payroll-Checker
I use this to check paryoll for basic things.

## Helpers Package
1. Basic functions to read data, get pay period number, and email.

## Not Started
1. Simply checks for people that haven't started their timesheet.
2. Will return a dict of KEY: manager_email and VALUE: employee_emails list.

## Employee Inprogress
1. Any employee still holding it on last Friday of pay period.

## Manager Pending
1. Any manager with pending timesheet.

## Overlapping Hours
1. Any hours that overlap except 'HLW', 'SHF'

## Bad Earn Codes
1. 'SHP', 'make up time', etc

## Hours In Excess Of Max
1. Non-union: 8 hours
2. Union: 7.5 hours