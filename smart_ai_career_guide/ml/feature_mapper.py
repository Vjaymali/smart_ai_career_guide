def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, float(value)))


def normalize_psychometric(score):
    try:
        return clamp((float(score) / 125) * 100)
    except (TypeError, ValueError):
        return 0


def text_from_answers(answers):
    values = []

    list_fields = [
        "favorite_subjects",
        "weak_subjects",
        "interests",
        "hobbies",
        "strengths",
        "career_goal"
    ]

    text_fields = [
        "qualification",
        "work_environment",
        "work_style",
        "work_life",
        "higher_studies",
        "relocation",
        "dream_job",
        "additional_info"
    ]

    for field in list_fields:
        value = answers.get(field, [])
        if isinstance(value, list):
            values.extend(str(x).lower() for x in value)
        elif value:
            values.append(str(value).lower())

    for field in text_fields:
        value = answers.get(field, "")
        if value:
            values.append(str(value).lower())

    return " ".join(values)


def keyword_score(text, keywords):
    if not text:
        return 0

    matches = sum(1 for keyword in keywords if keyword in text)

    if matches == 0:
        return 0

    return min(100, matches * 25)


def map_existing_data_to_ml_features(
    psychometric,
    answers
):
    """
    Convert the application's existing psychometric scores
    and Career Test answers into the features required by
    the trained ML model.

    This does not modify either test.
    """

    technical = normalize_psychometric(
        psychometric.get("technical_score", 0)
    )

    creative = normalize_psychometric(
        psychometric.get("creative_score", 0)
    )

    social = normalize_psychometric(
        psychometric.get("social_score", 0)
    )

    business = normalize_psychometric(
        psychometric.get("business_score", 0)
    )

    text = text_from_answers(answers)

    math_score = keyword_score(
        text,
        ["math", "mathematics", "statistics", "accounting", "economics"]
    )

    science_score = keyword_score(
        text,
        ["science", "physics", "chemistry", "biology"]
    )

    programming_score = keyword_score(
        text,
        ["programming", "programming skill", "coding", "software",
         "computer", "technology", "technology", "ai", "data"]
    )

    communication_score = keyword_score(
        text,
        ["communication", "writing", "speaking", "teaching",
         "leadership", "social", "people"]
    )

    logical_score = round(
        (technical + math_score + programming_score) / 3,
        2
    )

    return {
        "Math_Score": round((math_score + technical) / 2, 2),
        "Science_Score": round((science_score + technical) / 2, 2),
        "Programming_Skill": round(
            (programming_score + technical) / 2,
            2
        ),
        "Communication_Skill": round(
            (communication_score + social) / 2,
            2
        ),
        "Logical_Ability": logical_score,

        "R_score": technical,
        "I_score": technical,
        "A_score": creative,
        "S_score": social,
        "E_score": business,
        "C_score": round(
            (technical + business) / 2,
            2
        )
    }