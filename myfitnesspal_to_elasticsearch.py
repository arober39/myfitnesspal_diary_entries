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
    meals_json_object = json.dumps(json_object)
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
#        Prepare myfitnesspal data to send to ES
#                      or JSON file
# -----------------------------------------------------

def extract_name_of_meal(meal_string):
    # extract meal name
    spl_word2 = ','
    char_list = ['-', '(', ')']

    meal_split_at_comma = meal_string.partition(spl_word2)[0]

    for i in meal_split_at_comma:
        if i in char_list:
            meal_split_at_comma = meal_split_at_comma.replace(i, ' ')

    meal_name = " ".join(meal_split_at_comma.split())
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

def parse_each_meal_for_extraction(date, meal_type, totals):
    list_of_foods = []

    # outer dict
    outer_dict = {
        'date': date,
        'meal_type': meal_type['_name'],
        'total_meal_macros': totals,
        'list_of_food_macros': [],
        'list_of_foods': []
    }
    entries = meal_type['_entries']
    outer_outer_dict = {}
    macr = []
    for i in range(len(entries)):
        # extract food name
        food_name = extract_name_of_meal(str(entries[i]))
        list_of_foods.append(food_name)

        # create inner struct for each food
        macro_dict = grab_inner_dict_for_macros(entries, i, food_name, outer_dict)
        outer_dict['list_of_food_macros'].append(macro_dict)

    outer_dict['list_of_foods'] = list_of_foods

    return outer_dict


def structure_nutrition_data(dates):
    # iterate over list of dates
    for date in dates:
        # get the meals for the day
        myfitnesspal_day = client.get_date(date.year, date.month, date.day)

        if myfitnesspal_day:
            date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day)

            # send total calories and macros for the entire day to output function
            daily_total_dict = {
                'date': date_string,
                'daily_macros': myfitnesspal_day.totals
            }
        
            # send_todays_total_to_elasticsearch(daily_total_dict)
            send_todays_total_to_json_file(daily_total_dict)

            # get calories and macros for meals
            breakfast = myfitnesspal_day.meals[0]
            lunch = myfitnesspal_day.meals[1]
            dinner = myfitnesspal_day.meals[2]
            if breakfast and lunch and dinner:
                breakfast_dict = parse_each_meal_for_extraction(date_string, vars(breakfast), breakfast.totals)
                lunch_dict = parse_each_meal_for_extraction(date_string, vars(lunch), lunch.totals)
                dinner_dict = parse_each_meal_for_extraction(date_string, vars(dinner), dinner.totals)
           
            # send macros and calories for each meal to output function
            each_meals_macros_and_calories_output(breakfast_dict, lunch_dict, dinner_dict)

def main():
    
    start_date = date(2020, 12, 25)
    end_date = date(2021, 1, 3)
    
    delta = timedelta(days=1)
    dates = []
    while start_date <= end_date:
        dates.append(start_date)
        start_date += delta

    structure_nutrition_data(dates)

if __name__ == "__main__":
    main() 
