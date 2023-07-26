import json, jsonlines
import myfitnesspal
from datetime import date, timedelta
from elasticsearch import Elasticsearch
import configparser

config = configparser.ConfigParser()
config.read('mfp_elastic.ini')

# Elasticsearch client instance
es = Elasticsearch(
    cloud_id=config['ELASTIC']['cloud_id'],
    basic_auth=("elastic", config['ELASTIC']['password'])
)

es.info()

# myfitnesspal client
client = myfitnesspal.Client()

#---------------------------------------------------
#           Output - option 1 - JSON file
# --------------------------------------------------

# send breakfast, lunch, dinner structs to JSON file
def send_meals_to_json_file(json_object):
    meals_json_object = json.dumps(json_object, indent=4)
    meals_json = json.loads(meals_json_object)
    
    with open("meals_macros_calories.json", "a") as outfile:
        outfile.write(meals_json + ',')

# send each days overall calories and macros to JSON file
def send_todays_total_to_json_file(json_object):
    total_json_object = json.dumps(json_object, indent=4)
    total_json = json.loads(total_json_object)

    with open("macros_calories_overall.json", "a") as outfile:
        outfile.write(total_json_object + ',')

#---------------------------------------------------
#         Output - option 2 - Elasticsearch
# --------------------------------------------------

# send breakfast, lunch, dinner structs to ES
def send_meals_to_elasticsearch(meals_diary_entry):
    es.index(
        index='myfitnesspal_index',
        document=meals_diary_entry
    )

# send each days overall calories and macros to ES
def send_todays_total_to_elasticsearch(total_daily_entry):
    es.index(
        index='daily_myfitnesspal_total_index',
        document=total_daily_entry
    )

def total_daily_macros_and_calories_output(date, daily_totals_dict):
    daily_total_dict = {
        'date': date,
        'daily_macros': daily_totals_dict
    }
    # uncomment one of lines below when to send 
    # total macros and calories to either
    # elasticsearch index or JSON file

    # send_todays_total_to_elasticsearch(daily_total_dict)
    # send_todays_total_to_json_file(daily_total_dict)

def each_meals_macros_and_calories_output(breakfast_struct, lunch_struct, dinner_struct):
    breakfast_json_object = json.dumps(breakfast_struct)
    # send_meals_to_json_file(breakfast_json_object)
    # send_meals_to_elasticsearch(breakfast_json_object)

    lunch_json_object = json.dumps(lunch_struct)
    # send_meals_to_json_file(lunch_json_object)
    # send_meals_to_elasticsearch(lunch_json_object)

    dinner_json_object = json.dumps(dinner_struct)
    # send_meals_to_json_file(dinner_json_object)
    # send_meals_to_elasticsearch(dinner_json_object)

# -----------------------------------------------------
#        Combine data outputted from myfitnesspal 
#              client into a single struct
# -----------------------------------------------------

def extract_name_of_meal(meal_string):
    # extract meals
    spl_word = '{'
    spl_word2 = ','

    meal_split_at_bracket = meal_string.partition(spl_word)[0]
    meal_split_at_comma = meal_string.partition(spl_word2)[0]
    meal_remove_special_chars = meal_split_at_comma.replace('-', '')
    meal_remove_closing_parenthesis = meal_remove_special_chars.replace(')', '')
    meal_remove_opening_parenthesis = meal_remove_closing_parenthesis.replace('(', '')
    meal_name = " ".join(meal_remove_opening_parenthesis.split())

    return meal_name

def grab_inner_dict_for_macros(foods, item, item_name, outer_outer):
    temp_dict = {
        'food_macros': {}
    }
    nutrient_labels = ['calories', 'carbohydrates', 'fat', 'protein', 'sodium', 'sugar']

    temp_dict['name'] = item_name
    for j in nutrient_labels:
        temp_dict['food_macros'][j] = foods[item][j]

    return temp_dict

def parse_each_meal_for_extraction(foods, date, meal_type, totals):
    list_of_foods = []

    # outer dict
    outer_dict = {
        'date': date,
        'meal_type': meal_type['_name'],
        'total_macros': totals,
        'list_of_food_macros': [],
        'list_of_foods': []
    }
    
    outer_outer_dict = {}
    macr = []
    for i in range(len(foods)):
        # extract food name
        food_string = str(foods[i])
        food_name = extract_name_of_meal(food_string)
        list_of_foods.append(food_name)

        # create inner struct for each food
        macro_dict = grab_inner_dict_for_macros(foods, i, food_name, outer_dict)
        outer_dict['list_of_food_macros'].append(macro_dict)

    outer_dict['list_of_foods'] = list_of_foods

    return outer_dict


def structure_nutrition_data(year, month, day, date):
    if month[0] == '0':
        month = month[1]

    # get the meals per day
    myfitnesspal_day = client.get_date(int(year), int(month), int(day))

    if myfitnesspal_day:
        # get total calories and macros for the day
        total_daily_macros_and_calories_output(date, myfitnesspal_day.totals)

        # get calories and macros for each meal of the day
        breakfast = myfitnesspal_day.meals[0]
        lunch = myfitnesspal_day.meals[1]
        dinner = myfitnesspal_day.meals[2]
        breakfast_vars = vars(myfitnesspal_day.meals[0])
        lunch_vars = vars(myfitnesspal_day.meals[1])
        dinner_vars = vars(myfitnesspal_day.meals[2])
        breakfast_foods = breakfast.entries
        lunch_foods = lunch.entries
        dinner_foods = dinner.entries

        breakfast_dict = parse_each_meal_for_extraction(breakfast_foods, date, breakfast_vars, breakfast.totals)
        lunch_dict = parse_each_meal_for_extraction(lunch_foods, date, lunch_vars, lunch.totals)
        dinner_dict = parse_each_meal_for_extraction(dinner_foods, date, dinner_vars, dinner.totals)

        # send each meal dict to outputting function
        each_meals_macros_and_calories_output(breakfast_dict, lunch_dict, dinner_dict)
    else:
        print('found an empty struct')
        return

def parse_range_of_dates(dates):
    for item in dates:
        year = item[:4]
        month = item[5:7]
        day = item[8:]
        structure_nutrition_data(year, month, day, item)

def main():
    start_date = date(2020, 10, 1)
    end_date = date(2020, 10, 4)

    delta = timedelta(days=1)
    dates = []
    while start_date <= end_date:
        dates.append(start_date.isoformat())
        start_date += delta

    parse_range_of_dates(dates)

if __name__ == "__main__":
    main() 
