import os
import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv

HH_MOSCOW_AREA_ID = 1


def predict_salary(currency, expected_currency, salary_from, salary_to):
    if currency != expected_currency:
        return None
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from
    elif salary_to:
        return salary_to * 0.8
    return None


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get("salary")
    if not salary:
        return None
    return predict_salary(
        currency=salary.get("currency"),
        expected_currency="RUR",
        salary_from=salary.get("from"),
        salary_to=salary.get("to")
    )


def predict_rub_salary_sj(vacancy):
    return predict_salary(
        currency=vacancy.get("currency"),
        expected_currency="rub",
        salary_from=vacancy.get("payment_from"),
        salary_to=vacancy.get("payment_to")
    )


def analyze_hh(lang):
    salaries = []
    page = 0
    per_page = 100
    total_found = 0

    while True:
        params = {
            "text": f"{lang} программист",
            "area": HH_MOSCOW_AREA_ID,
            "per_page": per_page,
            "page": page
        }
        response = requests.get("https://api.hh.ru/vacancies", params=params)
        if not response.ok:
            break
        hh_response_data = response.json()
        vacancies = hh_response_data.get("items", [])
        total_found = hh_response_data.get("found", 0)

        for vacancy in vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salaries.append(salary)

        if page >= hh_response_data.get("pages", 0) - 1:
            break
        page += 1

    processed = len(salaries)
    average = int(sum(salaries) / processed) if processed else None
    return {
        "vacancies_found": total_found,
        "vacancies_processed": processed,
        "average_salary": average
    }


def analyze_superjob(lang, api_key):
    headers = {"X-Api-App-Id": api_key}
    salaries = []
    page = 0
    total_found = 0

    while True:
        params = {
            "keyword": f"{lang} программист",
            "count": 100,
            "page": page,
            "town": "Москва"
        }
        response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers, params=params)
        if not response.ok:
            break
        sj_response_data = response.json()
        vacancies = sj_response_data.get("objects", [])
        total_found += len(vacancies)

        for vacancy in vacancies:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                salaries.append(salary)

        if not sj_response_data.get("more") or len(salaries) >= 2000:
            break
        page += 1

    processed = len(salaries)
    average = int(sum(salaries) / processed) if processed else None
    return {
        "vacancies_found": total_found,
        "vacancies_processed": processed,
        "average_salary": average
    }


def build_salary_table(hh_stats, sj_stats, languages):
    table_data = [
        ["Язык", "HH: найдено / обработано", "SJ: найдено / обработано", "Зарплата HH / SJ"]
    ]

    for lang in languages:
        hh_lang_stats = hh_stats.get(lang, {})
        sj_lang_stats = sj_stats.get(lang, {})

        hh_found = hh_lang_stats.get("vacancies_found", 0)
        hh_proc = hh_lang_stats.get("vacancies_processed", 0)
        hh_salary = hh_lang_stats.get("average_salary", "—")

        sj_found = sj_lang_stats.get("vacancies_found", 0)
        sj_proc = sj_lang_stats.get("vacancies_processed", 0)
        sj_salary = sj_lang_stats.get("average_salary", "—")

        table_data.append([
            lang,
            f"{hh_found} / {hh_proc}",
            f"{sj_found} / {sj_proc}",
            f"{hh_salary} / {sj_salary}"
        ])

    return table_data


def main():
    load_dotenv()
    api_key = os.getenv("SUPERJOB_API_KEY")

    languages = ["Python", "Java", "JavaScript", "C#", "C++", "Go", "Ruby", "Swift", "PHP", "Kotlin"]

    hh_stats = {}
    sj_stats = {}

    for lang in languages:
        hh_stats[lang] = analyze_hh(lang)
        sj_stats[lang] = analyze_superjob(lang, api_key)

    table_data = build_salary_table(hh_stats, sj_stats, languages)
    table = AsciiTable(table_data, "Сравнение зарплат по языкам")
    print("\n" + table.table)


if __name__ == "__main__":
    main()