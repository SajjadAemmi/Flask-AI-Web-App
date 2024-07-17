from datetime import datetime, timedelta


def relative_time(datetime_str):
    # Parse the input string into a datetime object
    input_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
    
    # Get the current time
    current_time = datetime.now()
    
    # Calculate the difference
    time_difference = current_time - input_time
    
    # Determine the relative time
    seconds = time_difference.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minutes ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hours ago"
    else:
        days = int(seconds // 86400)
        return f"{days} days ago"
