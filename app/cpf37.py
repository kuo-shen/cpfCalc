def calculate_cpf(monthly_salary: float, age: int) -> dict:
    """
    Calculates CPF contributions with a $7,400 ceiling.
    Rates: 
    - 55 and below: 20% (Employee) / 17% (Employer)
    - 56 to 60: 15% (Employee) / 14% (Employer)
    """
    if monthly_salary < 0:
        raise ValueError("Salary cannot be negative.")
    if age < 16:
        raise ValueError("Age must be at least 16.")

    # Apply the $7,400 Ordinary Wage ceiling
    ow_ceiling = 7400
    subject_to_cpf = min(monthly_salary, ow_ceiling)

    if age <= 55:
        employee_rate = 0.20
        employer_rate = 0.17
    elif 56 <= age <= 60:
        employee_rate = 0.15
        employer_rate = 0.14
    else:
        # Defaulting to 56-60 rates for this scope, or could be extended for older ages
        employee_rate = 0.15
        employer_rate = 0.14

    employee_share = round(subject_to_cpf * employee_rate, 2)
    employer_share = round(subject_to_cpf * employer_rate, 2)
    total_contribution = round(employee_share + employer_share, 2)

    return {
        "employee_share": employee_share,
        "employer_share": employer_share,
        "total_contribution": total_contribution
    }

# Example usage:
if __name__ == "__main__":
    try:
        res = calculate_cpf(5000, 30)
        print(f"Age 30, $5000 Salary: {res}")
        res_older = calculate_cpf(8000, 58)
        print(f"Age 58, $8000 Salary (Capped at 7400): {res_older}")
    except ValueError as e:
        print(f"Error: {e}")