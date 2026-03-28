import csv
import json
import urllib.request
import datetime
import random
import os

# Configuration for Stoneham, MA
LATITUDE = 42.4801
LONGITUDE = -71.0995
WEATHER_API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=temperature_2m_max,precipitation_sum,snowfall_sum&temperature_unit=fahrenheit&precipitation_unit=inch&timezone=America%2FNew_York"

MEALS_CSV = "MealOptions.csv"
OUTPUT_HTML = "index.html"

def get_weather_forecast():
    """Fetches weather forecast for the next 14 days."""
    try:
        with urllib.request.urlopen(WEATHER_API_URL) as response:
            data = json.loads(response.read().decode())
            daily = data.get("daily", {})
            forecast = {}
            for i, date_str in enumerate(daily.get("time", [])):
                forecast[date_str] = {
                    "high_temp": daily.get("temperature_2m_max", [])[i],
                    "precip": daily.get("precipitation_sum", [])[i] + daily.get("snowfall_sum", [])[i]
                }
            return forecast
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None

def load_meals():
    """Loads meals from CSV file."""
    meals = []
    if not os.path.exists(MEALS_CSV):
        print(f"Error: {MEALS_CSV} not found.")
        return []
    
    with open(MEALS_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            meals.append({
                "name": row["Meal Name"].strip(),
                "protein": row["Protein"].strip(),
                "outside": row["Outside"].strip().lower() == "yes",
                "mexican": row["Mexican"].strip().lower() == "yes"
            })
    return meals

def generate_plan(meals, weather):
    """Generates a single valid meal plan for the week starting next Saturday."""
    today = datetime.date.today()
    # Find next Saturday
    days_ahead = (5 - today.weekday()) % 7
    if days_ahead <= 0: # If today is Sat, find next Sat? No, usually it's the following one.
        # But if the script runs Thursday, next Sat is in 2 days.
        days_ahead += 0 # Keep it as the very next Saturday
    
    # If today is Thursday, days_ahead is (5-3)%7 = 2.
    # So start_date is Thursday + 2 days = Saturday.
    start_date = today + datetime.timedelta(days=days_ahead)
    
    dates = [start_date + datetime.timedelta(days=i) for i in range(7)]
    days_of_week = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    
    # Required categories
    fixed_slots = ["Leftovers", "Pizza", "Premade Meal / Takeout"]
    
    # Shuffle slots
    all_indices = list(range(7))
    random.shuffle(all_indices)
    
    # Assign fixed slots to 3 random indices
    plan = [None] * 7
    fixed_indices = all_indices[:3]
    for i, name in zip(fixed_indices, fixed_slots):
        plan[i] = {"name": name, "protein": "None", "mexican": False, "outside": False}
    
    # Remaining 4 slots for meals from CSV
    remaining_indices = sorted(all_indices[3:])
    
    # Constraints:
    # 1. Monday (index 2) or Tuesday (index 3) must be Mexican.
    # 2. One Pork, One Chicken, One (Beef or Fish).
    # 3. No consecutive repeat proteins.
    # 4. Outside meals only if weather > 45 and precip == 0.
    
    def is_valid(current_plan):
        # 4. Consecutive proteins check
        for i in range(1, 7):
            if current_plan[i] and current_plan[i-1]:
                if current_plan[i]["protein"] != "None" and current_plan[i]["protein"] == current_plan[i-1]["protein"]:
                    return False
        
        # 5. Outside check
        for i, meal in enumerate(current_plan):
            if meal and meal["outside"]:
                date_str = dates[i].isoformat()
                w = weather.get(date_str)
                if not w or w["high_temp"] <= 45 or w["precip"] > 0:
                    return False
        return True

    # Backtracking or simple randomized search
    attempts = 0
    while attempts < 1000:
        attempts += 1
        trial_plan = list(plan)
        available_meals = list(meals)
        random.shuffle(available_meals)
        
        success = True
        for idx in remaining_indices:
            found_meal = False
            for m in available_meals:
                # Check consecutive protein rule immediately
                prev_protein = trial_plan[idx-1]["protein"] if idx > 0 and trial_plan[idx-1] else None
                next_protein = trial_plan[idx+1]["protein"] if idx < 6 and trial_plan[idx+1] else None
                
                if m["protein"] == prev_protein or m["protein"] == next_protein:
                    continue
                
                # Check weather if outside
                if m["outside"]:
                    date_str = dates[idx].isoformat()
                    w = weather.get(date_str)
                    if not w or w["high_temp"] <= 45 or w["precip"] > 0:
                        continue
                
                trial_plan[idx] = m
                available_meals.remove(m)
                found_meal = True
                break
            
            if not found_meal:
                success = False
                break
        
        if success:
            # Check mandatory rules
            proteins_in_plan = [m["protein"] for m in trial_plan if m]
            has_pork = "Pork" in proteins_in_plan
            has_chicken = "Chicken" in proteins_in_plan
            has_beef_fish = ("Beef" in proteins_in_plan or "Fish" in proteins_in_plan)
            
            mon_tue_mexican = (trial_plan[2] and trial_plan[2]["mexican"]) or (trial_plan[3] and trial_plan[3]["mexican"])
            
            if has_pork and has_chicken and has_beef_fish and mon_tue_mexican:
                return list(zip(days_of_week, dates, trial_plan))
                
    return None

def generate_html(plans):
    """Generates an HTML file with the meal plan options."""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Weekly Meal Plan</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; line-height: 1.6; background-color: #fafafa; color: #333; }}
        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
        h1 {{ text-align: center; color: #2c3e50; margin-bottom: 5px; }}
        .subtitle {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 0.9em; }}
        .option {{ margin-bottom: 40px; padding: 25px; border: 1px solid #edf2f7; border-radius: 12px; background-color: #fff; }}
        .option h2 {{ margin-top: 0; color: #3498db; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 20px; }}
        .day {{ margin-bottom: 12px; font-size: 1.1em; }}
        .day b {{ color: #2d3748; }}
        .weather-info {{ font-size: 0.85em; color: #718096; margin-left: 10px; }}
        @media (max-width: 480px) {{
            .container {{ padding: 15px; }}
            .day b {{ display: block; margin-bottom: 2px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Dinner Menu</h1>
        <p class="subtitle">Generated on {datetime.date.today().strftime('%B %d, %Y')}</p>
"""
    if not plans:
        html_content += "<p>Could not generate enough valid meal plans. Please check constraints or add more meal options.</p>"
    else:
        for i, plan in enumerate(plans):
            html_content += f"""
        <div class="option">
            <h2>Option {i+1}</h2>
"""
            for day_name, date, meal in plan:
                html_content += f"""
            <div class="day">
                <b>{day_name}</b>: {meal['name']}
            </div>
"""
            html_content += "        </div>"

    html_content += """
    <p style="text-align: center; font-size: 0.8em; color: #a0aec0;">&copy; Meal Plan Generator</p>
    </div>
</body>
</html>
"""
    with open(OUTPUT_HTML, "w", encoding='utf-8') as f:
        f.write(html_content)
    print(f"Generated {OUTPUT_HTML}")

def main():
    weather = get_weather_forecast()
    if not weather:
        print("Failed to get weather. Proceeding with caution (assuming all days > 45F and dry).")
        weather = {}
        
    meals = load_meals()
    if not meals:
        return

    plans = []
    seen_plans = set()
    
    attempts = 0
    while len(plans) < 3 and attempts < 100:
        attempts += 1
        plan = generate_plan(meals, weather)
        if plan:
            # Create a unique key for the plan to avoid duplicates
            plan_key = tuple(m['name'] for _, _, m in plan)
            if plan_key not in seen_plans:
                seen_plans.add(plan_key)
                plans.append(plan)
    
    generate_html(plans)

if __name__ == "__main__":
    main()
