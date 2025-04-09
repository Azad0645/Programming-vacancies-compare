import os
import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv


HH_MOSCOW_AREA_ID = 1


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get("salary")
    if salary and salary.get("currency") == "RUR":
        salary_from = salary.get("from")
        salary_to = salary.get("to")
        if salary_from and salary_to:
            return (salary_from + salary_to) / 2
        elif salary_from:
            return salary_from
        elif salary_to:
            return salary_to * 0.8
    return None


def predict_rub_salary_sj(vacancy):
    if vacancy.get("currency") != "rub":
        return None
    salary_from = vacancy.get("payment_from")
    salary_to = vacancy.get("payment_to")
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from
    elif salary_to:
        return salary_to * 0.8
    return None


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
        if response.status_code != 200:
            break
        data = response.json()
        vacancies = data.get("items", [])
        total_found = data.get("found", 0)

        for vacancy in vacancies:
            salary = predict_rub_salary_hh(vacancy)
            if salary:
                salaries.append(salary)

        if page >= data.get("pages", 0) - 1:
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
        if response.status_code != 200:
            break
        data = response.json()
        vacancies = data.get("objects", [])
        total_found += len(vacancies)

        for vacancy in vacancies:
            salary = predict_rub_salary_sj(vacancy)
            if salary:
                salaries.append(salary)

        if not data.get("more") or len(salaries) >= 2000:
            break
        page += 1

    processed = len(salaries)
    average = int(sum(salaries) / processed) if processed else None
    return {
        "vacancies_found": total_found,
        "vacancies_processed": processed,
        "average_salary": average
    }


def main():
    load_dotenv()
    api_key = os.getenv("SUPERJOB_API_KEY")

    languages = ["Python", "Java", "JavaScript", "C#", "C++", "Go", "Ruby", "Swift", "PHP", "Kotlin"]

    hh_data = {}
    sj_data = {}

    table_data = [
        ["Язык", "HH: найдено / обработано", "SJ: найдено / обработано", "Зарплата HH / SJ"]
    ]

    for lang in languages:
        hh_data[lang] = analyze_hh(lang)
        sj_data[lang] = analyze_superjob(lang, api_key)
        hh = hh_data.get(lang, {})
        sj = sj_data.get(lang, {})

        hh_found = hh.get("vacancies_found", 0)
        hh_proc = hh.get("vacancies_processed", 0)
        hh_salary = hh.get("average_salary", "—")

        sj_found = sj.get("vacancies_found", 0)
        sj_proc = sj.get("vacancies_processed", 0)
        sj_salary = sj.get("average_salary", "—")

        table_data.append([
            lang,
            f"{hh_found} / {hh_proc}",
            f"{sj_found} / {sj_proc}",
            f"{hh_salary} / {sj_salary}"
        ])

    table = AsciiTable(table_data, "Сравнение зарплат по языкам")
    print("\n" + table.table)

if __name__ == "__main__":
    main()