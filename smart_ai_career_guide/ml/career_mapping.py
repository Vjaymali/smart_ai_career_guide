ML_TO_APP_CAREERS = {
    "Accountant": "Chartered Accountant",
    "Doctor": "Doctor (MBBS)",
    "Teacher": "Teacher/Educator",
    "Software Engineer": "Software Developer",
    "Data Scientist": "Data Scientist",
    "Entrepreneur": "Entrepreneur"
}


def map_ml_career_to_app_career(ml_career):
    return ML_TO_APP_CAREERS.get(ml_career)