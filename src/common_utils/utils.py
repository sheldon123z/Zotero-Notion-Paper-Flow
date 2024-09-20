def generate_key(prefix, current_max_number):
    """
    Generate a key with a given prefix followed by a number which increments.

    Args:
        prefix (str): The prefix for the key.
        current_max_number (int): The current maximum number used after the prefix.

    Returns:
        str: A new key with the incremented number.
    """
    # Increment the number
    next_number = current_max_number + 1
    
    # Generate the new key
    new_key = f"{prefix}{next_number:04d}"  # 04d ensures the number is padded with zeros to 4 digits
    return new_key

# Example usage
current_max_number = 2345
prefix = "ABCD"
new_key = generate_key(prefix, current_max_number)
print(new_key)  # Output should be "ABCD2346"