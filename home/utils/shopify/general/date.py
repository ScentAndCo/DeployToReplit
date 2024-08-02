from datetime import datetime

def next_month_10th():
    today = datetime.today()
    year = today.year
    month = today.month

    # Calculate the next month
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

    # Create the date for the 10th of the next month
    next_month_date = datetime(year, month, 10)

    return next_month_date