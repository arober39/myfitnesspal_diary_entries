# Send myfitnessal data to Elasticsearch

![Screenshot](myfitnesspalKibana.png)

## Setup
As outlined in python-myfitnesspal [documentation](https://python-myfitnesspal.readthedocs.io/en/latest/getting_started.html), we first need to install the package
```
pip install myfitnesspal
```

I also found it complained the typing extensions package was missing. If that happens, simply install that as well
```
pip install typing-extensions
```

Since the myfitnesspal package uses cookies to log in from the terminal, we will have to grant the [terminal full disk access](https://osxdaily.com/2018/10/09/fix-operation-not-permitted-terminal-error-macos/). Ensure you grant access to a browser you've prevously used to log into myfitnesspal.

## Pass date range

```
def main():

    start_date = date(2020, 10, 1)
    end_date = date(2020, 10, 2)
```

## Option 1 - Store results in JSON file
1. First, create two separate json files 
- "macros_calories_overall.json" - to store total calories and macros for the day
- "meals_macros_calories.json" - to store calories and macros for each meal of that day

2. Uncomment function calls in both output functions to send nutrition data to two seperate JSON files

Quick note: remove last comma in json file and wrap entire output in braces to denote list of objects

```
def total_daily_macros_and_calories_output(date, daily_totals_dict):
    daily_total_dict = {
        'date': date,
        'daily_macros': daily_totals_dict
    }

    # send_todays_total_to_elasticsearch(daily_total_dict)
    send_todays_total_to_json_file(daily_total_dict)

def each_meals_macros_and_calories_output(breakfast_struct, lunch_struct, dinner_struct):
    breakfast_json_object = json.dumps(breakfast_struct)
    send_meals_to_json_file(breakfast_json_object)
    # send_meals_to_elasticsearch(breakfast_json_object)

    lunch_json_object = json.dumps(lunch_struct)
    send_meals_to_json_file(lunch_json_object)
    # send_meals_to_elasticsearch(lunch_json_object)

    dinner_json_object = json.dumps(dinner_struct)
    send_meals_to_json_file(dinner_json_object)
    # send_meals_to_elasticsearch(dinner_json_object)
```

## Option 2 - Send JSON to Elasticsearch and store as index
To send data to ES using the python client, you will first need:

1. An [Elastic Cloud account](https://cloud.elastic.co/).
2. A new file ```mfp_elastic.ini``` with cloud_id, username, and password as shown [here](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/connecting.html).

Then, uncomment function calls in both output functions to send nutrition data to ES

```
def total_daily_macros_and_calories_output(date, daily_totals_dict):
    daily_total_dict = {
        'date': date,
        'daily_macros': daily_totals_dict
    }

    send_todays_total_to_elasticsearch(daily_total_dict)
    # send_todays_total_to_json_file(daily_total_dict)

def each_meals_macros_and_calories_output(breakfast_struct, lunch_struct, dinner_struct):
    breakfast_json_object = json.dumps(breakfast_struct)
    # send_meals_to_json_file(breakfast_json_object)
    send_meals_to_elasticsearch(breakfast_json_object)

    lunch_json_object = json.dumps(lunch_struct)
    # send_meals_to_json_file(lunch_json_object)
    send_meals_to_elasticsearch(lunch_json_object)

    dinner_json_object = json.dumps(dinner_struct)
    # send_meals_to_json_file(dinner_json_object)
    send_meals_to_elasticsearch(dinner_json_object)
```