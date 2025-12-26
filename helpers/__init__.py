"""
helpers package

A collection of utility modules for the Payroll Checker application.

This package provides helper functions for payroll processing including:
    - data loading and manipulation
    - pay period detection and calculation
    - email notification functionality via Outlook

Modules:
    data: Loads CSV files into pandas DataFrames for processing.
    pay_period_detector: Calculates the current pay period based on the year.
    win32com_email: Manages email notifications using Outlook via win32com.

Dependencies:
    - pandas (for data module)
    - win32com (for email module)
"""
