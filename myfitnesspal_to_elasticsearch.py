
import myfitnesspal
from datetime import date, timedelta
from elasticsearch import Elasticsearch
import json
import configparser


config = configparser.ConfigParser()
config.read('mfp_elastic.ini')

# Elasticsearch client instance
es_client = Elasticsearch(
    cloud_id=config['ELASTIC']['cloud_id'],
    basic_auth=("elastic", config['ELASTIC']['password'])
)

es_client.info()

# myfitnesspal client
client = myfitnesspal.Client()

#---------------------------------------------------
#           Output - option 1 - JSON file
# --------------------------------------------------

# send breakfast, lunch, dinner structs to JSON file
def send_meals_to_json_file(json_object):
    if json_object:
        meals_json_object = json.dumps(json_object, indent=4)
        meals_json = json.loads(meals_json_object)
        print(meals_json)
        with open("meals_macros_calories.json", "a") as outfile:
            outfile.write(meals_json + ',')
    return

# send each days overall calories and macros to JSON file
def send_todays_total_to_json_file(json_object):
    if json_object:
        total_json_object = json.dumps(json_object, indent=4)
        total_json = json.loads(total_json_object)

        with open("macros_calories_overall.json", "a") as outfile:
            outfile.write(total_json_object + ',')
    return

#---------------------------------------------------
#         Output - option 2 - Elasticsearch
# --------------------------------------------------

# send breakfast, lunch, dinner structs to ES
def send_meals_to_elasticsearch(meals_diary_entry):
    if meals_diary_entry:
        es_client.index(
            index='myfitnesspal_diary_for_each_meal_index',
            document=meals_diary_entry
        )
    return

# send each days overall calories and macros to ES
def send_todays_total_to_elasticsearch(total_daily_entry):
    if total_daily_entry:
        es_client.index(
            index='daily_myfitnesspal_for_each_day_index',
            document=total_daily_entry
        )
    return

# -----------------------------------------------------
#        Prepare myfitnesspal data to send to ES
#                      or JSON file
# -----------------------------------------------------

def extract_name_of_meal(meal_string):
    # extract meal name
    spl_word = ','
    char_list = ['-', '(', ')']

    meal_split_at_comma = meal_string.partition(spl_word)[0]

    for i in meal_split_at_comma:
        if i in char_list:
            meal_split_at_comma = meal_split_at_comma.replace(i, ' ')

    meal_name = " ".join(meal_split_at_comma.split())
    return meal_name

def grab_inner_dict_for_macros(foods, item, item_name):
    temp_dict = {
        'food_macros': {}
    }
    nutrient_labels = ['calories', 'carbohydrates', 'fat', 'protein', 'sodium', 'sugar']

    temp_dict['name'] = item_name
    for j in nutrient_labels:
        temp_dict['food_macros'][j] = foods[item][j]

    return temp_dict

def parse_each_meal_for_extraction(date, meal, meal_totals):
    outer_dict = {
        'date': date,
        'meal_type': meal['_name'],
        'total_meal_macros': meal_totals,
        'list_of_food_macros': [],
        'list_of_foods': []
    }
    food_names_lst = []
    entries = meal['_entries']
  
    for i in range(len(entries)):
        # extract food name
        food_name = extract_name_of_meal(str(entries[i]))
        food_names_lst.append(food_name)

        # create inner struct for each food
        macro_dict = grab_inner_dict_for_macros(entries, i, food_name)
        outer_dict['list_of_food_macros'].append(macro_dict)

    outer_dict['list_of_foods'] = food_names_lst

    return outer_dict


def structure_nutrition_data(dates):
    # iterate over list of dates
    for date in dates:
        # get the meals for the day
        myfitnesspal_day = client.get_date(date.year, date.month, date.day)
        date_str = str(date)

        if myfitnesspal_day:
            date_string = str(date.year) + '-' + str(date.month) + '-' + str(date.day)
            # send total calories and macros for the entire day to output function
            if myfitnesspal_day.totals == {}:
                print("No entries for this day")
                return
            else:
                daily_total_dict = {
                    'date': date_str,
                    'daily_macros': myfitnesspal_day.totals
                }
            # send_todays_total_to_json_file(daily_total_dict)
            # send_todays_total_to_elasticsearch(daily_total_dict)

            # get calories and macros for meals
            breakfast = myfitnesspal_day.meals[0]
            lunch = myfitnesspal_day.meals[1]
            dinner = myfitnesspal_day.meals[2]
            snacks = myfitnesspal_day.meals[3]


            if breakfast:
                 breakfast_dict = parse_each_meal_for_extraction(date_str, vars(breakfast), breakfast.totals)
            else:
                breakfast_dict = {}
                print("No breakfast entries for " + date_str)

            if lunch:
                lunch_dict = parse_each_meal_for_extraction(date_str, vars(lunch), lunch.totals)
            else:
                lunch_dict = {}
                print("No lunch entries for " + date_str)

            if dinner:
                dinner_dict = parse_each_meal_for_extraction(date_str, vars(dinner), dinner.totals)
            else:
                dinner_dict = {}
                print("No dinner entries for " + date_str)

            if snacks:
                snacks_dict = parse_each_meal_for_extraction(date_str, vars(snacks), snacks.totals)
            else:
                snacks_dict = {}
                print("No snack entries for " + date_str)

            # send macros and calories for each meal to output function
            if breakfast_dict != {}:
                breakfast_json_object = json.dumps(breakfast_dict)
                # send_meals_to_json_file(breakfast_json_object)
                # send_meals_to_elasticsearch(breakfast_json_object)

            if lunch_dict != {}:
                lunch_json_object = json.dumps(lunch_dict)
                # send_meals_to_json_file(lunch_json_object)
                # send_meals_to_elasticsearch(lunch_json_object)

            if dinner_dict != {}:
                dinner_json_object = json.dumps(dinner_dict)
                # send_meals_to_json_file(dinner_json_object)
                # send_meals_to_elasticsearch(dinner_json_object)

            if snacks_dict != {}:
                snacks_json_object = json.dumps(snacks_dict)
                # send_meals_to_json_file(snacks_json_object)
                # send_meals_to_elasticsearch(snacks_json_object)
            

def main():
    
    start_date = date(2022, 10, 1)
    end_date = date(2022, 10, 1)
    
    delta = timedelta(days=1)
    dates = []
    while start_date <= end_date:
        dates.append(start_date)
        start_date += delta

    structure_nutrition_data(dates)

if __name__ == "__main__":
    main() 
